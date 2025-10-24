from typing import List

import numpy
from blissdata.h5api import dynamic_hdf5


def read_counters(
    filename: str,
    scan_number: int,
    subscan_number: int,
    counters: List[str],
    **retry_options,
) -> List[numpy.ndarray]:
    with dynamic_hdf5.File(filename, mode="r", **retry_options) as nxroot:
        scan = nxroot[f"{scan_number}.{subscan_number}"]
        _ = scan["end_time"]  # wait until scan is finished
        measurement = scan["measurement"]
        data = [measurement[name][()] for name in counters]
    nmin = min(len(values) for values in data)
    return [values[:nmin] for values in data]
