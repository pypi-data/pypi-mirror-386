"""
A parent class that defines a common interface for all filter implementations.

Authors:
    | Tim J. Kuhlbusch <tim[dot]kuhlbusch[at]rwth-aachen.de>
    | Artem Basalaev <artem[dot]basalaev[at]pm.me>
"""
from typing import Type, TypeVar, Iterable, Optional
from warnings import warn
from copy import deepcopy
from pathlib import Path
import json
from dataclasses import dataclass, asdict

import numpy as np
from gwpy.timeseries import TimeSeriesDict

from spicypy.signal.time_series import TimeSeries

# create a type variable that can be any instance of a Filter subclass
FilterType = TypeVar("FilterType", bound="Filter")


@dataclass
class Filter:  # pylint: disable=too-many-instance-attributes
    """Parent class for filter implementations.
    Using this ensures a consistent interface for all filters and minimizes duplicate code.

    Function overloading by children must implement all non-optional parameters in the same position and order to guarantee compatibility.
    This is also enforced through a common test suite.

        Parameters
        ----------
        test:
            The signal that the filter will try to approximate.
        reference:
            Witness signal(s) to which the filter is applied.
        n_taps:
            Number of taps of the filter. This is equivalent to the number of time steps of the reference signal processed to get one prediction sample.
        n_proc: optional
            Number of parallel processes to use. Defaults to number of CPUs.
        subtract_mean: optional
            Subtract mean from data for internal processing, to ensure that floating point numbers are not too large. For the output time series operation is inverted, therefore besides improving numerical stability it is not affecting the results. Defaults to true.
        normalize_data: optional
            Divide data by its standard deviation for internal processing, to ensure that floating point numbers are not too large. For the output time series operation is inverted, therefore besides improving numerical stability it is not affecting the results. Defaults to true.
    """

    # The values defined here will be exported in the JSON dump
    # through the asdict() method and this being a dataclass.
    # Values in the parent class may not have default values, due to the way dataclasses work.
    test_mean: float
    test_std: float
    refs_mean: Iterable[float]
    refs_std: Iterable[float]
    reference_format: Optional[list]

    sample_rate: float
    n_references: int
    unit: str

    n_taps: int
    subtract_mean: bool
    normalize_data: bool

    def __init__(  # pylint: disable=too-many-positional-arguments
        self,
        test: TimeSeries,
        reference: TimeSeriesDict | list,
        n_taps: int | None = None,
        subtract_mean: bool = True,
        normalize_data: bool = True,
        _from_dict: dict | None = None,
        **_kwargs,  # these will be ignored, except when
    ) -> None:
        # If _from_dict is passed, all other values will be ignored and the class will be initialized based on the dict content.

        self.subtract_mean = True
        self.normalize_data = True

        self.json_keys = [
            "sample_rate",
            "test_std",
            "test_mean",
            "refs_std",
            "refs_mean",
            "n_taps",
            "subtract_mean",
            "normalize_data",
            "n_references",
            "unit",
        ]
        self.optional_json_keys = [
            "reference_format",
        ]
        if hasattr(self, "additional_json_keys"):
            self.json_keys += list(self.additional_json_keys)

        if _from_dict is not None:
            self.loaded_from_file = True
            for key in self.json_keys:
                setattr(self, key, _from_dict.get(key))
            for key in self.optional_json_keys:
                if key in _from_dict:
                    setattr(self, key, _from_dict.get(key))
                else:
                    setattr(self, key, None)
            return
        else:
            self.loaded_from_file = False

        # The target time series.
        self.test = test
        # The witness signals.
        if isinstance(reference, TimeSeriesDict):
            self.reference_format = list(reference)
            self.reference = list(reference.values())
        elif isinstance(reference, list):
            self.reference_format = None
            self.reference = reference
        else:
            raise TypeError(
                "only TimeSeriesDict or list of TimeSeries are supported types for reference time series"
            )

        self.n_taps = n_taps or (len(self.test) - 1)
        self.subtract_mean = subtract_mean
        self.normalize_data = normalize_data

        # make a list of all inputs and compare values to test consistency
        inputs_list = self.reference + [self.test]
        self._check_timeseries_consistency(inputs_list)

        # copy time series parameters to filter properties
        self.sample_rate = self.test.sample_rate.value
        self.n_references = len(self.reference)
        self.unit = self.test.unit.to_string()

        self._check_mandatory_inputs()

    def _check_mandatory_inputs(self):
        """Check the input parameters for consistency."""
        if self.n_taps <= 0:
            raise ValueError(
                "You must specify a non-zero number of taps for the filter."
            )
        if self.n_taps >= 15000:
            warn(
                "Creating a filter with 15000 or more taps requested. This is A LOT. Depending on number of "
                "references and available resources, calculation may fail!"
            )
        if self.n_taps + 1 > len(self.test):
            warn(
                "Cannot set more taps than input time series length - 1. Setting n_taps to time series length - 1. "
            )
            self.n_taps = len(self.test) - 1

    def _check_timeseries_consistency(self, inputs_list):
        """Check input time series consistency (sampling rates, start time, length, etc.).

        Parameters
        ----------
        inputs_list: `list` of `TimeSeries`
            input time series
        """

        sample_rate = inputs_list[0].sample_rate.value
        epoch = inputs_list[0].epoch
        n_samples = len(inputs_list[0])

        # test time series for consistency
        for input_time_series in inputs_list:
            if len(input_time_series) != n_samples:
                raise ValueError(
                    "All time series must have the same length (number of samples)!"
                )
            if input_time_series.sample_rate.value != sample_rate:
                raise ValueError("All time series must have the same sampling rate!")
            if (
                input_time_series.epoch is not None
                and epoch is not None
                and input_time_series.epoch != epoch
            ):
                raise ValueError(
                    "All time series must be aligned in time (same time_series.epoch)!"
                )
            if np.iscomplexobj(input_time_series.value):
                raise NotImplementedError(
                    "Filtering for complex time series is not implemented."
                )

    def _prepare_data(self):
        """
        Normalize input time series to values close to 1 if requested, for better numerical stability.
        Subtract mean if requested.
        """

        self.test_array = deepcopy(self.test.value)  # need to copy time series
        # or else normalization will affect original values

        self.test_mean = np.mean(self.test_array)
        self.test_std = np.std(self.test_array)

        self.reference_array = np.array(self.reference, copy=True).T
        self.refs_mean = np.mean(self.reference_array, axis=0)
        self.refs_std = np.std(self.reference_array, axis=0)

        if self.subtract_mean:
            self.test_array -= self.test_mean
            self.reference_array -= self.refs_mean
        if self.normalize_data:
            self.test_array /= self.test_std
            self.reference_array /= self.refs_std

    @staticmethod
    def _make_json_filname(filename: str) -> Path:
        """Append the `.json` suffix to the given filename if it does not already have it."""
        # convert to Path object and append file ending if necessary
        path = Path(filename)
        if path.suffix != ".json":
            path = Path(filename + ".json")
        return path

    def save(self, filename: str):
        """Save the filter as a JSON text file.

        Parameters
        ----------
        filename:
            Target filename. If file name does not end in `.json`, it will be appended.
        """
        with open(self._make_json_filname(filename), "w", encoding="utf-8") as out_file:
            filter_dict = self.as_dict()
            filter_dict = {
                k: (v.tolist() if isinstance(v, np.ndarray) else v)
                for k, v in filter_dict.items()
            }
            json.dump(filter_dict, out_file, default=str)

    @classmethod
    def load(cls: Type[FilterType], filename: str) -> FilterType:
        """Load the filter from a JSON text file.

        Parameters
        ----------
        filename: `str`
            Target filename. If file name does not end on `.json`, it will be appended.

        Returns
        -------
        New filter object.
        """
        with open(
            Filter._make_json_filname(filename), "r", encoding="utf-8"
        ) as in_file:
            data_dict = json.load(in_file)

        # All other arguments are ignored if _from_dict is supplied.
        # The values here are just placeholders to match the signature of the user facing inializer.
        return cls(TimeSeries([]), [], n_taps=1, _from_dict=data_dict)

    def as_dict(self) -> dict:
        """Return a JSON compatible dict representation of the filter."""
        return asdict(self)

    def create_filters(self) -> None:  # TODO: this does not work as a generic name!
        """A function that must be called by the user after instantiating the class. This function conditions the filter based on the input provided during instantiation."""
        raise NotImplementedError(
            "create_filters() must be implemented by child class."
        )

    def _preprocess_data(self, to_training_data, inputs_list):
        """Preprocess data (check, normalize, subtract mean, etc) before applying the filter.

        Parameters
        ----------
        to_training_data: `bool`
            Whether the filter is applied to training data.
        inputs_list: `np.array` of `float`
            Array of inputs (references) to which this filter is applied.

        Returns
        -------
        refs: `Iterable[np.array]`
            The prepared reference signal.
        """

        if (inputs_list is None and not to_training_data) or (
            inputs_list is not None and to_training_data
        ):
            raise ValueError(
                "Either a reference time series must be specified or 'to_training_data' set to 'True', but not both."
            )

        if to_training_data:
            return self.reference_array

        if self.n_taps >= len(inputs_list[0]):
            raise ValueError(
                "Input time series has less time steps than number of filter taps! Cannot apply filter."
            )

        # check consistency
        self._check_timeseries_consistency(inputs_list)
        if inputs_list[0].sample_rate.value != self.sample_rate:
            raise ValueError(
                f"Reference sample rate is not the same as sample rate used to generate this filter (expected {self.sample_rate}, got {inputs_list[0].sample_rate.value})!"
            )

        if len(inputs_list) != self.n_references:
            raise ValueError("Wrong number of references for this Filter")

        refs = np.array(inputs_list, copy=True).T

        for i in range(refs.shape[1]):
            if self.normalize_data:
                refs[:, i] /= self.refs_std[i]
            if self.subtract_mean:
                refs[:, i] -= self.refs_mean[i]
        return refs

    @staticmethod
    def _check_apply_parameters(func):
        """Decorator for create_filters() impelementations that checks the mandatory parameters.

        Converts inputs_list from TimeSeriesDict to list.
        """

        def wrapper(self, inputs_list=None, *args, **kwargs):
            to_training_data = kwargs.get("to_training_data") or (
                args[2] if len(args) > 2 else False
            )

            if to_training_data and self.loaded_from_file:
                raise NotImplementedError(
                    "Cannot apply filter to training data because this filter "
                    "was loaded from file; filters are already applied to training data earlier. "
                    "Try calling `.apply(..)` without `to_training_data` argument."
                )

            # if the reference values given at apply were a TimeSeriesDict
            if not to_training_data:
                if self.reference_format is None:
                    if isinstance(inputs_list, TimeSeriesDict):
                        raise ValueError(
                            "This filter was not initialized from a TimeSeriesDict and does not accept a TimeSeriesDict as inputs_list."
                        )
                else:
                    if not isinstance(inputs_list, TimeSeriesDict):
                        raise ValueError(
                            "This filter was initialized from a TimeSeriesDict and only accepts TimeSeriesDict for inputs_list."
                        )

                    inputs_list = [inputs_list[key] for key in self.reference_format]

            return func(self, inputs_list, *args, **kwargs)

        return wrapper

    @_check_apply_parameters
    def apply(
        self,
        inputs_list: Optional[Iterable[TimeSeries]] = None,
        zero_padding: bool = True,
        normalized_output: bool = False,
        to_training_data: bool = False,
        use_multiprocessing: bool = False,
    ):  # pylint: disable=too-many-positional-arguments
        """Apply the filter to given input data.
        inputs_list: `list` of `TimeSeries` or `TimeSeriesDict`, optional
            time series to apply filter to, not needed if applying to training data
        zero_padding: `bool`, optional
            if true, return time series of the same length as inputs,
            with zeros in the beginning (filter needs to "accumulate" data equal to its n_taps first);
            if false, returned time series will be shorter and with shifted t0 by n_taps/sample_rate
        normalized_output: `bool`, optional
            if true, do not add mean and multiply by standard deviation, as if the data were already normalized
        to_training_data: `bool`, optional
            apply filters to training data - runs after filter creation to de3termine best filter,
            but can also be called explicitly
        use_multiprocessing: `bool`, optional
            Whether to use multiprocessing (with number of parallel processes set with `self.n_proc`)

        Returns
        -------
        prediction :  `TimeSeries`
            filter output
        """
        raise NotImplementedError("apply() must be implemented by child class.")
