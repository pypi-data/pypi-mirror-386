"""
Wrapper for LPSD method, see https://gitlab.com/uhh-gwd/lpsd

| Artem Basalaev <artem[dot]basalaev[at]pm.me>
| Christian Darsow-Fromm <cdarsowf[at]physnet.uni-hamburg.de>
"""

from warnings import warn

import inspect
import pandas as pd
import numpy as np

from lpsd import lcsd
from lpsd._lcsd import LCSD
from gwpy.signal.spectral._utils import scale_timeseries_unit

from spicypy.signal.frequency_series import FrequencySeries


def lpsd(*args, **kwargs):  # pylint: disable=too-many-branches
    """Calculate the CSD of a `TimeSeries` using LPSD method.

    Parameters
    ----------
    args : `list`
        timeseries: `TimeSeries`
            input time series (if only one specified, calculates PSD)
        other: `TimeSeries`, optional
            second input time series
        nfft: `int`
            number of samples per FFT, user-specified value ignored; calculated by the algorithm instead

    kwargs : dict
        fftlength : `float`, optional
            number of seconds in single FFT. User-specified value ignored, algorithm calculates optimal segment lengths.
        overlap : `float`, optional
            number of seconds of overlap between FFTs.
        window : `str`, optional
            Window function to apply to timeseries prior to FFT. Possible values: 'hann', 'hanning', 'ham', 'hamming', 'bartlett', 'blackman', 'kaiser'. Defaults to 'kaiser'.
        additional arguments are passed to :class:`lpsd.lcsd`

    Returns
    -------
    fs: FrequencySeries
        resulting CSD
    """

    try:
        timeseries, nfft = args
        other = timeseries
    except ValueError:
        timeseries, other, nfft = args

    if len(timeseries.value) != len(other.value):
        raise ValueError("Time series must have the same length (number of samples)!")

    # No fftlength for LPSD method.
    if kwargs.get("fftlength") or nfft != len(timeseries.value):
        warn(
            "fftlength/nfft arguments are not supported by LPSD averaging method; "
            "segment lengths are calculated by the algorithm."
        )

    # convert overlap given in number of seconds to percentage
    overlap = kwargs.pop("overlap", 0)
    if overlap > 0:
        total_duration = timeseries.duration
        if overlap > total_duration:
            raise ValueError(
                "Specified overlap (in seconds) exceeds total time series duration!"
            )
        overlap = overlap / total_duration

    # convert window to numpy function
    window = kwargs.pop("window_", None)
    window = "kaiser" if window is None else window
    # clean up default value from kwargs
    if "window" in kwargs:
        kwargs.pop("window")
    if not isinstance(window, str):
        warn(
            "Specifying window as an array for Daniell averaging method is not supported, defaulting to 'hann' window"
        )
        window = "kaiser"

    window_to_func = {
        "kaiser": np.kaiser,
        "hann": np.hanning,
        "hanning": np.hanning,
        "hamm": np.hamming,
        "hamming": np.hamming,
        "bartlett": np.bartlett,
        "blackman": np.blackman,
    }
    try:
        window_function = window_to_func[window]
    except KeyError as exc:
        raise KeyError(
            "Window " + window + "is not supported for LPSD averaging method"
        ) from exc

    # Convert inputs to pandas.DataFrame
    df = pd.DataFrame()
    df["x1"] = timeseries.value
    df["x2"] = other.value
    df.index = timeseries.times.value

    # clean up kwargs: get ones that are allowed for LPSD
    allowed_kwargs = inspect.getfullargspec(LCSD.__init__).args
    lpsd_kwargs = kwargs.copy()
    for k in kwargs:
        if k not in allowed_kwargs:
            lpsd_kwargs.pop(k)
    csd = lcsd(df, overlap=overlap, window_function=window_function, **lpsd_kwargs)

    # generate FrequencySeries and return
    unit = scale_timeseries_unit(
        timeseries.unit,
        kwargs.pop("scaling", "density"),
    )
    fs = FrequencySeries(
        csd["psd"].values,
        unit=unit,
        frequencies=csd.index.values,
        name=timeseries.name,
        epoch=timeseries.epoch,
        channel=timeseries.channel,
    )
    return fs
