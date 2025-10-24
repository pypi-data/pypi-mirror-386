from dataclasses import dataclass

import numpy

from .bliss import read_counters


@dataclass
class TemperatureData:
    filename: str
    scan_number: int
    label: str
    epoch: numpy.ndarray  # shape: (nPoints,)
    wavelength: numpy.ndarray  # units: nm, shape: (nPoints, nWavelength)
    response: numpy.ndarray  # shape: (nPoints, nWavelength)
    planck_data: numpy.ndarray  # shape: (nPoints, nWavelength)
    planck_fit: numpy.ndarray  # shape: (nPoints, nWavelength)
    planck_fit_slice: slice
    planck_temperature: numpy.ndarray  # units:K, shape: (nPoints,)


def read_temperature_data(
    filename: str,
    scan_number: int,
    subscan_number: int,
    laser_id: str,
    label: str,
    **retry_options,
) -> TemperatureData:
    laser_prefix = "laser_heating"
    laser_counters = [
        "spectrum_lambdas",
        "max_data",
        "planck_data",
        "planck_fit",
        "T_planck",
    ]
    counters = ["epoch"] + [
        f"{laser_prefix}_{laser_id}_{ctr}" for ctr in laser_counters
    ]
    keys = [
        "epoch",
        "wavelength",
        "response",
        "planck_data",
        "planck_fit",
        "planck_temperature",
    ]
    data = read_counters(
        filename, scan_number, subscan_number, counters, **retry_options
    )
    data = dict(zip(keys, data))

    not_zero = numpy.any(numpy.abs(data["planck_fit"]) > 1, axis=0)
    fit_indices = numpy.where(not_zero)[0]
    data["planck_fit_slice"] = slice(fit_indices[0], fit_indices[-1] + 1)

    return TemperatureData(
        filename=filename, scan_number=scan_number, label=label, **data
    )
