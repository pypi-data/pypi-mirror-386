"""
Class creating Wiener filter from reference time series to signal time series.

Wiener filter gives an estimate of target channel from one or more references, based on linear coherence.
This estimate is optimal for linear and stationary signals. The most common application is to have reference(s) for
noise which enables then subtraction of this noise from target channel. More generally, Wiener filter generates
a time-domain filter that is equivalent to frequency-domain transfer function between two channels, or several such
transfer functions if more than one reference is used (one per reference).

The most common Wiener filter algorithm available (e.g. in image processing etc) relies on one reference, or
even no reference if noise is being estimated directly in the target channel. In other words it is a single-input,
single-output Wiener filter, or sometimes the output has higher dimensionality, such as the case with filtering
images (2D). MISO filter (based on algorithm in https://dcc.ligo.org/LIGO-T070192/public), where multiple references
can be supplied to estimate target channel. See also `J. Harms, Terrestrial gravity fluctuations, Living Reviews in
Relativity 22, 6 (2019)`.

This complicates the calculation as the matrix to invert is no longer a simple Toeplitz matrix,
but a block-Toeplitz matrix. This structure however is still exploited to speed up calculation significantly compared
to general matrix inversion. Implementation is based on iterative solvers from `scipy.sparse.linalg` that don't require
full matrix knowledge for every iteration and `scipy.sparse.linalg.LinearOperator` to generate matrix elements based on
a rule (operator), which permits exploiting symmetries of the matrix. In case of longer time series than necessary for
filter generation, several filters will be generated and the best automatically selected. Application of the filter
to references is also optimized using `numpy` arrays and optionally can be done with `multiprocessing`.

Authors:
    | Artem Basalaev <artem[dot]basalaev[at]pm.me>
    | Tim J. Kuhlbusch <tim[dot]kuhlbusch[at]rwth-aachen.de>
"""
from copy import copy
from typing import Iterable
import multiprocessing
from dataclasses import dataclass, asdict

import numpy as np

# import LinearOperator and all sorts of different solvers
from scipy.sparse.linalg import (
    LinearOperator,
    gmres,
    cgs,
    cg,
    gcrotmk,
    tfqmr,
    bicgstab,
    lgmres,
    minres,
)
from scipy.signal import correlate, correlation_lags
from scipy.linalg import matmul_toeplitz
from scipy import optimize
from spicypy.signal.time_series import TimeSeries
from spicypy.signal import Filter

_solver_list = {
    "gmres": gmres,
    "cgs": cgs,
    "cg": cg,
    "gcrotmk": gcrotmk,
    "tfqmr": tfqmr,
    "bicgstab": bicgstab,
    "lgmres": lgmres,
    "minres": minres,
}


@dataclass
class WienerFilter(Filter):  # pylint: disable=too-many-instance-attributes
    """
    Class creating Wiener filter from reference time series to signal time series.

        Parameters
        ----------
        test: `TimeSeries`
            input time series
        reference: `list`, `TimeSeriesDict`
            reference time series
        kwargs : `dict`
            n_taps : `int`
                Number of taps for this Wiener filter, should be less than time series length.
            zero_padding : `bool`, optional
                Whether to use zero padding; if set to true, resulting time series will begin at the same time as input time series, but will be filled with zeros for n_taps (default: true).
            use_multiprocessing : `bool`, optional
                Whether to use multiprocessing to apply filters (default:false).
            n_proc: `int`, optional
                Number of parallel processes to use. Defaults to number of CPUs.
            subtract_mean: `bool`, optional
                Subtract mean from data for internal processing, to ensure that floating point numbers are not too large. For the output time series operation is inverted, therefore besides improving numerical stability it is not affecting the results. Defaults to true.
            normalize_data: `bool`, optional
                Divide data by its standard deviation for internal processing, to ensure that floating point numbers are not too large. For the output time series operation is inverted, therefore besides improving numerical stability it is not affecting the results. Defaults to true.
            use_norm_factor: `bool`, optional
                Renormalize resulting Wiener filter by finding the best-fitting normalization coefficient for ASD on training data. May result in improvement in case of MISO filter with noisy references, otherwise not recommended. Defaults to false.
            verbose: `bool`, optional
                Enable verbose output (default: false).
            solver: `str`, optional
                Solver to use for Wiener-Hopf equations. Default: `tfqmr`. Other available: `gmres`, `cgs`, `cg`, `gcrotmk`, `tfqmr`, `bicgstab`, `lgmres`, `minres`.
    """

    # the values defined here will be exported in the JSON dump
    # through the asdict() method and this being a dataclass
    W: dict
    best_filter_index: int
    kwargs: dict
    norm_factor: dict
    normalize: bool
    use_norm_factor: bool
    zero_padding: bool
    solver = None
    solver_arg: str
    verbose: bool

    filter_name: str = "WienerFilter"
    additional_json_keys: Iterable[str] = (
        "W",
        "best_filter_index",
        "kwargs",
        "norm_factor",
        "normalize",
        "use_norm_factor",
        "zero_padding",
        "solver",
        "solver_arg",
        "verbose",
        "filter_name",
    )

    def __init__(self, test, reference, **kwargs):
        """Init method for Wiener filter"""
        super().__init__(test, reference, **kwargs)

        self.use_multiprocessing = kwargs.pop("use_multiprocessing", False)
        self.verbose = kwargs.pop("verbose", False)

        if self.loaded_from_file:
            # NOTE: this might not be the best way to handle the whole keys become strings
            # through the json dump thing..
            self.W = {int(k): np.array(v) for k, v in self.W.items()}
            self.norm_factor = {int(k): v for k, v in self.norm_factor.items()}
            self.best_filter_index = int(
                self.best_filter_index
            )  # old save files have this index as a string value
            self.initialized = True
            return

        self.kwargs = kwargs
        self.test_array = None
        self.reference_array = None

        self.unique_rmi = {}
        self.P = {}
        self.labels = {}
        self.W = {}
        self.norm_factor = {}
        self.test_std = 1.0
        self.test_mean = 0.0
        self.refs_std = []
        self.refs_mean = []
        self.best_filter_index = 0

        self._check_inputs()
        # Note for following attributes: they are needed only to be able to use pool.map(..) function and
        # pass information which normally would be done with function arguments. Maybe there's a nicer way to do it.
        self.parallel_idx = None
        self.parallel_slice_length = None
        self.parallel_filter_index = None
        self.parallel_refs = None

        self.initialized = False  # to indicate whether create_filters() was called

    def _check_inputs(self):
        """Parse input arguments for this Wiener filter."""

        if self.loaded_from_file:  # Do nothing; no inputs to check if loaded from file
            return

        # make a list of all inputs and compare values to test
        inputs_list = self.reference + [self.test]
        self._check_timeseries_consistency(inputs_list)
        self.sample_rate = self.test.sample_rate.value
        self.n_references = len(self.reference)
        self.unit = self.test.unit.to_string()

        # get parameters for Wiener filter calculation
        self.zero_padding = self.kwargs.pop("zero_padding", True)
        self.n_proc = self.kwargs.pop("n_proc", multiprocessing.cpu_count())
        if self.n_proc == 1:
            self.use_multiprocessing = False
        self.subtract_mean = self.kwargs.pop("subtract_mean", True)
        self.normalize = self.kwargs.pop("normalize_data", True)
        self.use_norm_factor = self.kwargs.pop("use_norm_factor", False)

        self.solver = tfqmr
        self.solver_arg = self.kwargs.pop("solver", "tfqmr")
        if self.solver_arg in _solver_list:
            self.solver = _solver_list[self.solver_arg]
        else:
            raise NotImplementedError(
                "Requested solver " + self.solver_arg + " is not supported"
            )
        if self.use_norm_factor and self.normalize:
            raise NotImplementedError(
                "Additional norm factor can only be derived"
                " when Wiener filter is applied to already normalized data"
            )

    def save(self, filename: str):
        """Save the filter as a JSON text file.

        Parameters
        ----------
        filename:
            Target filename. If file name does not end in `.json`, it will be appended.
        """
        if not self.initialized:
            raise RuntimeError(
                "save() can only be called on an instance that has been initialized by executing create_filters()!"
            )
        super().save(filename)

    def create_filters(self):
        """Calculate Wiener filter(s) based on inputs."""
        self.initialized = True

        if self.loaded_from_file:
            raise NotImplementedError(
                "Cannot generate filters because this Wiener filter was loaded from file;"
                " filters are already generated earlier. Try calling `.apply(..)` instead."
            )
        self._prepare_data()
        # each filter requires n_taps + 1 time steps to create
        if len(self.test) > (
            2 * self.n_taps
        ):  # will create multiple filters and choose the best one
            # first calculate how many times n_taps
            n_filters = int(np.floor(len(self.test) / self.n_taps))
            # then check if there's one more time step for last filter, if not make one less
            if len(self.test) <= n_filters * self.n_taps:
                n_filters -= 1
            print("Creating Wiener Filters...")
            for i in range(n_filters):
                self._create_filter(
                    i,
                    self.test_array,
                    self.reference_array,
                    i * self.n_taps,
                    (i + 1) * self.n_taps,
                )
            self.determine_best_filter()
        else:  # create one filter
            self._create_filter(
                0, self.test_array, self.reference_array, 0, self.n_taps
            )

    def as_dict(self) -> dict:
        """Return a JSON compatible dict representation of the filter."""
        filter_dict = asdict(self)
        filter_dict["W"] = {k: v.tolist() for k, v in filter_dict["W"].items()}
        return filter_dict

    def determine_best_filter(self):
        """Find the best-performing Wiener Filter on input data."""

        if self.loaded_from_file:
            raise NotImplementedError(
                "Cannot determine the best filter because this Wiener filter was "
                "loaded from file; best filters are already found earlier. "
                "Try calling `.apply(..)` instead."
            )

        print("Determining the best filter...")
        mse_arr = np.zeros(len(self.W))
        test_asd = self.test.asd(method="lpsd")
        for idx in self.W:
            result_ts = self.apply(
                inputs_list=None,
                index=idx,
                zero_padding=True,
                normalized_output=True,
                to_training_data=True,
            )
            result_asd = result_ts.asd(method="lpsd")
            mse = 0.0
            if self.use_norm_factor:

                def MSE_to_minimize(norm_factor):
                    return MSE(
                        test_asd.value,
                        norm_factor
                        * result_asd.value,  # pylint: disable=cell-var-from-loop
                    )

                norm = optimize.minimize_scalar(MSE_to_minimize)
                self.norm_factor[idx] = norm.x
                mse = MSE_to_minimize(norm.x)
                if self.verbose:
                    print(
                        idx,
                        "MSE:",
                        MSE_to_minimize(norm.x),
                        "normalization factor:",
                        norm.x,
                    )
            else:
                mse = MSE(test_asd.value, result_asd.value)
                if self.verbose:
                    print(idx, "MSE:", mse)
            mse_arr[idx] = mse
        self.best_filter_index = np.argmin(mse_arr)
        print("Done. Best filter index:", self.best_filter_index)

    def _create_filter(
        self, index, tot_signal, tot_refs, start, end
    ):  # pylint: disable=too-many-positional-arguments
        """Calculate individual Wiener filter

        Parameters
        ----------
        index: `int`
            Current filter index.
        tot_signal: `np.array` of `float`
            Target time series, which filter should recreate.
        tot_refs: `np.array` of `float`
            One or multiple reference time series.
        start: `int`
            First index in the array for this filter.
        end: `int`
            Last index in the array for this filter.
        """

        if self.verbose:
            print("Creating Wiener filter: ", index)
        signal = tot_signal[start : end + 1]
        refs = tot_refs[start : end + 1]
        n_refs = refs.shape[1]

        self._wiener_components(refs, signal, index)
        unique_rmi = self.unique_rmi[index]
        unique_colrows = unique_rmi.shape[0]
        labels = self.labels[index]

        def R_block_times_vec(q, r, vec):
            colrow_idx = None
            transpose = False
            for i in range(unique_colrows):
                if labels[i][0] == q and labels[i][1] == r:
                    colrow_idx = i
                    break
                if q != r and labels[i][0] == r and labels[i][1] == q:
                    colrow_idx = i
                    transpose = True
                    break
            if colrow_idx is None:
                raise ValueError("Block ", q, r, "is out of bounds!")
            rmi_left = unique_rmi[colrow_idx][0 : self.n_taps + 1]
            rmi_right = unique_rmi[colrow_idx][self.n_taps :]
            if transpose:
                return matmul_toeplitz((rmi_right, np.flip(rmi_left)), vec)
            return matmul_toeplitz((np.flip(rmi_left), rmi_right), vec)

        def R_times_vec(vec):
            vec = np.ndarray.flatten(vec)
            outvec = np.zeros(shape=vec.shape[0])
            for i in range(n_refs):
                for j in range(n_refs):
                    outvec[
                        i * (self.n_taps + 1) : (i + 1) * (self.n_taps + 1)
                    ] = outvec[
                        i * (self.n_taps + 1) : (i + 1) * (self.n_taps + 1)
                    ] + R_block_times_vec(
                        i, j, vec[j * (self.n_taps + 1) : (j + 1) * (self.n_taps + 1)]
                    )
            return outvec

        operator_dim = (self.n_taps + 1) * refs.shape[1]
        Rv = LinearOperator(shape=(operator_dim, operator_dim), matvec=R_times_vec)
        if self.verbose:
            print("inverting the matrix")
        W = self.solver(Rv, self.P[index])
        self.W[index] = W[0]

    def _wiener_components(self, refs, signal, index):
        """Prepare components for the Wiener-Hopf equations: covariance matrix, cross-corr vector.

        Parameters
        ----------
        refs: `np.array` of `float`
            One or multiple reference time series.
        signal: `np.array` of `float`
            Target time series, which filter should recreate.
        index: `int`
            Current filter index.
        """

        n_refs = refs.shape[1]
        n_time_steps = refs.shape[0]

        # unique components ("rmi") rows/cols of covariance matrix
        unique_colrows = n_refs * (n_refs + 1) // 2
        colrow_length = 2 * (self.n_taps + 1) - 1
        unique_rmi = np.zeros(shape=(unique_colrows, colrow_length))

        # input covariance matrix
        lags = correlation_lags(n_time_steps, n_time_steps)
        max_lag = np.where(np.abs(lags) <= self.n_taps)
        k = 0
        for m in range(n_refs):
            for i in range(m, n_refs):
                if self.verbose:
                    print("calculating R" + str(m) + str(i))
                rmi = correlate(refs[:, m], refs[:, i])
                rmi = np.ndarray.flatten(np.take(rmi, max_lag))
                unique_rmi[k, :] = rmi
                k = k + 1

        # cross−correlation vector
        P = np.zeros(n_refs * (self.n_taps + 1))
        if self.verbose:
            print("calculating cross-corr vector")
        for i in range(n_refs):
            top = i * (self.n_taps + 1)
            bottom = (i + 1) * (self.n_taps + 1)
            p = correlate(signal, refs[:, i])
            p = np.ndarray.flatten(np.take(p, max_lag))
            P[top:bottom] = np.conjugate(p[self.n_taps :])

        k = 0
        labels = np.zeros(shape=(unique_colrows, 2), dtype=np.int8)
        for m in range(n_refs):
            for i in range(m, n_refs):
                labels[k] = [m, i]
                k = k + 1

        self.unique_rmi[index] = unique_rmi
        self.P[index] = P
        self.labels[index] = labels

    def _apply_parallel(self, i):
        """Apply Wiener filter to partial data by one parallel process.
        Can be called once to apply to all data by a single process.

        Parameters
        ----------
        i: `int`
            index of the parallel process (default: 0 for single process)
        """

        n_time_steps = self.parallel_refs.shape[0]
        n_refs = self.parallel_refs.shape[1]
        W = self.W[self.parallel_filter_index]
        indices = self.parallel_idx[
            self.parallel_slice_length * i : self.parallel_slice_length * (i + 1)
        ]
        result_timeseries = np.zeros(n_time_steps)

        for n in indices:  # time steps for which we can calculate
            # output signal
            if self.verbose and n % 50000 == 0:
                print(
                    "Applying filter " + str(self.parallel_filter_index) + ": step",
                    n - self.n_taps,
                    "out of",
                    n_time_steps - self.n_taps,
                )
            for m in range(n_refs):  # number of ref channels
                result_timeseries[n] = result_timeseries[n] + W[
                    (self.n_taps + 1) * m : (self.n_taps + 1) * (m + 1)
                ].dot(np.flip(self.parallel_refs[n - self.n_taps : n + 1, m]))
        return indices, result_timeseries

    def _post_process_data(  # pylint: disable=too-many-positional-arguments
        self,
        result_timeseries,
        zero_padding,
        to_training_data,
        normalized_output,
        index,
        inputs_list,
    ):
        """Post-process data (revert normalization, package as `TimeSeries`, etc.).

        Parameters
        ----------
        result_timeseries: `np.array` of `float`
            Raw time series - result of the applied filter
        zero_padding: `bool`
            Whether to add zeros in front (results in time series of same length as input).
        to_training_data: `bool`
            Whether the filter was applied to training data.
        normalized_output: `bool`
            Whether the data were normalized before creating filter - in that case inverse should be applied to the result.
        index: `int`
            Index of the applied filter, in case it has individual norm factor to be applied.
        inputs_list: `np.array` of `float`
            Array of inputs (references) to which this filter is applied.
        """

        if not zero_padding:
            result_timeseries = result_timeseries[self.n_taps :]

        unit = self.unit
        if to_training_data:
            t0 = copy(self.test.t0)
            sample_rate = self.test.sample_rate
        else:
            t0 = copy(inputs_list[0].t0)
            sample_rate = inputs_list[0].sample_rate

        if not zero_padding:  # advance start time by filter length
            t0 += self.n_taps / sample_rate

        if not normalized_output:
            norm_factor = 1.0
            if index in self.norm_factor:
                norm_factor = self.norm_factor[index]
                if self.verbose:
                    print("Multiplying by norm factor=", norm_factor)
            result_timeseries *= norm_factor
            if self.normalize:
                result_timeseries = result_timeseries * self.test_std
                if self.verbose:
                    print("Multiplying by test std=", self.test_std)
            if self.subtract_mean:
                result_timeseries += self.test_mean
                if self.verbose:
                    print("Adding mean=", self.test_mean)

        return TimeSeries(
            result_timeseries,
            sample_rate=sample_rate,
            unit=unit,
            t0=t0,
            name="Wiener filter output",
        )

    @Filter._check_apply_parameters
    def apply(  # pylint: disable=too-many-positional-arguments
        self,
        inputs_list=None,
        zero_padding=None,
        normalized_output=False,
        to_training_data=False,
        use_multiprocessing=None,
        index=None,
    ):
        """Apply Wiener filter to data.

        Parameters
        ----------
        inputs_list: `list` of `TimeSeries`, optional
            time series to apply Wiener filter to, not needed if applying to training data
        index: `int`, optional
            use specific Wiener filter by index, by default using the best filter determined earlier
        zero_padding: `bool`, optional
            if true, return time series of the same length as inputs,
            with zeros in the beginning (Wiener filter needs to "accumulate" data equal to its n_taps first);
            if false, returned time series will be shorter and with shifted t0 by n_taps/sample_rate
        normalized_output: `bool`, optional
            if true, do not add mean and multiply by standard deviation, as if the data were already normalized
        to_training_data: `bool`, optional
            apply filters to training data - runs after filter creation to de3termine best filter,
            but can also be called explicitly
        use_multiprocessing: `bool`, optional
            use multiprocessing (with number of parallel processes set with `self.n_proc`)

        Returns
        -------
        prediction :  `TimeSeries`
            Wiener filter output
        """
        if not self.initialized:
            raise RuntimeError(
                "apply() can only be called on an instance that has been initialized by executing create_filters()!"
            )

        if use_multiprocessing is None:
            use_multiprocessing = self.use_multiprocessing

        if index is None:  # apply the best filter
            index = self.best_filter_index

        refs = self._preprocess_data(to_training_data, inputs_list)

        n_time_steps = refs.shape[0]
        idx = np.arange(
            self.n_taps, n_time_steps
        )  # time steps for which we can calculate output signal
        self.parallel_idx = idx
        self.parallel_filter_index = index
        self.parallel_refs = refs

        if use_multiprocessing and len(idx) < self.n_proc:
            print(
                "Requested multiprocessing but time series is not long enough to benefit from it. "
                "You can try to set n_proc to lower values to run on fewer processes than "
                + str(self.n_proc)
                + ". Running in single process mode."
            )
        if use_multiprocessing and len(idx) > self.n_proc:
            print(
                "Using multiprocessing. Your computer may become unresponsive due to load, this is expected. Please "
                "wait until the operation is complete."
            )
            self.parallel_slice_length = int(np.ceil(len(idx) / float(self.n_proc)))
            n_slices = int(np.ceil(len(idx) / float(self.parallel_slice_length)))
            result_timeseries = np.zeros(self.parallel_refs.shape[0])

            with multiprocessing.Pool(processes=self.n_proc) as pool:
                result_list = pool.map(self._apply_parallel, range(n_slices))
            for indices, ts in result_list:
                result_timeseries[indices[0] : indices[-1]] = ts[
                    indices[0] : indices[-1]
                ]

        else:
            self.parallel_slice_length = len(idx)
            _, result_timeseries = self._apply_parallel(0)

        if zero_padding is None:
            zero_padding = self.zero_padding

        return self._post_process_data(
            result_timeseries,
            zero_padding,
            to_training_data,
            normalized_output,
            index,
            inputs_list,
        )


def MSE(sig_asd, pred_asd):
    """Calculate mean squared error on FrequencySeries

    Parameters
    ----------
    sig_asd: `FrequencySeries`
        "signal" frequency series
    pred_asd: `FrequencySeries`
        "prediction" frequency series

    Returns
    -------
    mse :  float
        mean squared error
    """
    return np.mean(np.square(sig_asd - pred_asd))
