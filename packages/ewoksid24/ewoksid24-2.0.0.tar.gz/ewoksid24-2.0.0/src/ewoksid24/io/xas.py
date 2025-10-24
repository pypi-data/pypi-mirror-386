from dataclasses import dataclass

import numpy

from .bliss import read_counters


@dataclass
class XasData:
    filename: str
    scan_number: int
    epoch: numpy.ndarray
    energy: numpy.ndarray  # keV
    mu: numpy.ndarray


def read_xas_data(
    filename: str, scan_number: int, energy_name: str, mu_name: str, **retry_options
) -> XasData:
    counters = ["epoch", energy_name, mu_name]
    epoch, energy, mu = read_counters(
        filename, scan_number, 1, counters, **retry_options
    )
    return XasData(
        filename=filename, scan_number=scan_number, epoch=epoch, energy=energy, mu=mu
    )
