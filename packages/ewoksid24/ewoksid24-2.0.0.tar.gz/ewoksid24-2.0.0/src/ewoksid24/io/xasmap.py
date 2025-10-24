import logging
from dataclasses import dataclass
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple

import h5py
import numpy
from silx.io import h5py_utils

_logger = logging.getLogger(__name__)


@dataclass
class XasMapData:
    mu: numpy.ndarray  # shape (npts, nenergy)
    energy: numpy.ndarray  # shape (npts, nenergy)
    x0: numpy.ndarray  # shape (npts,)
    x1: numpy.ndarray  # shape (npts,)
    x0_name: str
    x1_name: str
    energy_units: Optional[str] = None
    x0_units: Optional[str] = None
    x1_units: Optional[str] = None

    def is_empty(self) -> bool:
        return (
            self.mu.size == 0
            or self.energy.size == 0
            or self.x0.size == 0
            or self.x1.size == 0
        )


@dataclass
class _AccumulateData:
    mu: List[numpy.ndarray]  # npts x shape (nenergy,)
    energy: List[numpy.ndarray]  # npts x shape (nenergy,)
    x0: List[numpy.ndarray]  # shape (npts,)
    x1: List[numpy.ndarray]  # shape (npts,)
    energy_units: Optional[str] = None
    x0_units: Optional[str] = None
    x1_units: Optional[str] = None

    def extend(self, other: "_AccumulateData") -> None:
        self.mu.extend(other.mu)
        self.energy.extend(other.energy)
        self.x0.extend(other.x0)
        self.x1.extend(other.x1)
        self.energy_units = self.energy_units or other.energy_units
        self.x0_units = self.x0_units or other.x0_units
        self.x1_units = self.x1_units or other.x1_units


def read_xasmap(
    filenames: Sequence[str],
    dim0_counter: str,
    dim1_counter: str,
    energy_counter: str,
    mu_counter: str,
    scan_ranges: Optional[Sequence[Optional[Tuple[int, int]]]] = None,
    exclude_scans: Optional[Sequence[Optional[Sequence[int]]]] = None,
    subscan: int = 1,
) -> XasMapData:
    xasmapdata = _AccumulateData(
        mu=list(),
        energy=list(),
        x0=list(),
        x1=list(),
    )

    if not scan_ranges:
        scan_ranges = [None] * len(filenames)
    if not exclude_scans:
        exclude_scans = [None] * len(filenames)

    for filename, scan_range, exclude_scans in zip(
        filenames, scan_ranges, exclude_scans
    ):
        file_xasmapdata = _read_xasmap_file(
            filename,
            dim0_counter,
            dim1_counter,
            energy_counter,
            mu_counter,
            scan_range=scan_range,
            exclude_scans=exclude_scans,
            subscan=subscan,
        )
        xasmapdata.extend(file_xasmapdata)

    return XasMapData(
        mu=numpy.array(xasmapdata.mu),
        energy=numpy.array(xasmapdata.energy),
        x0=numpy.array(xasmapdata.x0),
        x1=numpy.array(xasmapdata.x1),
        x0_name=dim0_counter,
        x1_name=dim1_counter,
        energy_units=xasmapdata.energy_units,
        x0_units=xasmapdata.x0_units,
        x1_units=xasmapdata.x1_units,
    )


def _read_xasmap_file(
    filename: str,
    dim0_counter: str,
    dim1_counter: str,
    energy_counter: str,
    mu_counter: str,
    scan_range: Optional[Tuple[int, int]] = None,
    exclude_scans: Optional[Sequence[int]] = None,
    subscan: int = 1,
) -> _AccumulateData:
    with h5py_utils.File(filename) as nxroot:
        scans = sorted(int(scan.split(".")[0]) for scan in nxroot)
        if scan_range:
            scans = [nr for nr in scans if nr >= scan_range[0] and nr <= scan_range[1]]
        if exclude_scans:
            scans = [nr for nr in scans if nr not in exclude_scans]

        xasmapdata = _AccumulateData(
            mu=list(),
            energy=list(),
            x0=list(),
            x1=list(),
        )

        for scan in scans:
            uri = f"{filename}::/{scan}.{subscan}"
            try:
                scan_xasmapdata = _read_xas_scan(
                    nxroot,
                    scan,
                    subscan,
                    uri,
                    dim0_counter,
                    dim1_counter,
                    energy_counter,
                    mu_counter,
                )
                xasmapdata.extend(scan_xasmapdata)
            except Exception:
                _logger.exception("Error in scan %r", uri)

    return xasmapdata


def _read_xas_scan(
    nxroot: h5py.Group,
    scan: int,
    subscan: int,
    uri: str,
    dim0_counter: str,
    dim1_counter: str,
    energy_counter: str,
    mu_counter: str,
) -> _AccumulateData:
    xasmapdata = _AccumulateData(
        mu=list(),
        energy=list(),
        x0=list(),
        x1=list(),
    )

    # Scan group (Nxentry)
    entry_name = f"{scan}.{subscan}"
    if entry_name not in nxroot:
        _logger.warning("BLISS scan does not exist (%r)", uri)
        return xasmapdata
    nxentry = nxroot[entry_name]
    end_reason = _get_scan_end_reason(nxentry)

    # Measurement group (counters)
    if "measurement" not in nxentry:
        if end_reason:
            _logger.warning("Skip BLISS scan %r (%s)", uri, end_reason)
        else:
            _logger.warning("BLISS scan has no 'measurement' group (%r)", uri)
        return xasmapdata
    measurement = nxentry["measurement"]

    # mu vs. energy
    if energy_counter not in measurement:
        _logger.warning("BLISS scan has no '%s' counter (%r)", energy_counter, uri)
        return xasmapdata
    if mu_counter not in measurement:
        _logger.warning("BLISS scan has no '%s' counter (%r)", mu_counter, uri)
        return xasmapdata
    energy_dset = measurement[energy_counter]
    mu_dset = measurement[mu_counter]

    # Map axes
    x0_dset = None
    x1_dset = None
    if dim0_counter in measurement and dim1_counter in measurement:
        # Bug in ID24-ED dmap: 0D in positioners instead of 1D
        x0_dset = measurement[dim0_counter]
        x1_dset = measurement[dim1_counter]
    elif "instrument/positioners" in nxentry:
        positioners = nxentry["instrument/positioners"]
        if dim0_counter in positioners and dim1_counter in positioners:
            x0_dset = positioners[dim0_counter]
            x1_dset = positioners[dim1_counter]
    if x0_dset is None:
        _logger.warning(
            "BLISS scan has no '%s' or '%s' counter (%r)",
            dim0_counter,
            dim1_counter,
            uri,
        )
        return xasmapdata

    # Shapes (npts, nenergy) or (npts,) or (nenergy,)
    x0_data = _extract_data(x0_dset)
    x1_data = _extract_data(x1_dset)
    energy_data = _extract_data(energy_dset)
    mu_data = _extract_data(mu_dset)

    # Shape (npts,)
    if x0_data.ndim != 1:
        raise ValueError(f"{dim0_counter!r} must be 1D ({uri})")
    if x1_data.ndim != 1:
        raise ValueError(f"{dim1_counter!r} must be 1D ({uri})")

    if mu_data.ndim == 1:
        # One scan == one XAS spectrum
        if end_reason and end_reason != "SUCCESS":
            _logger.warning("Skip single XAS scan %r (%s)", uri, end_reason)
            return xasmapdata

        if energy_data.ndim != 1:
            raise ValueError(f"{energy_counter!r} must be 1D ({uri})")
        if x0_data.size != 1:
            raise ValueError(f"{dim0_counter!r} must be 0D ({uri})")
        if x1_data.size != 1:
            raise ValueError(f"{dim1_counter!r} must be 0D ({uri})")
        xasmapdata = _parse_single_xas_data(
            energy_data,
            mu_data,
            x0_data,
            x1_data,
        )
    else:
        # One scan == many XAS spectra
        xasmapdata = _parse_multi_xas_data(
            energy_data,
            mu_data,
            x0_data,
            x1_data,
        )

    xasmapdata.energy_units = energy_dset.attrs.get("units")
    xasmapdata.x0_units = x0_dset.attrs.get("units")
    xasmapdata.x1_units = x1_dset.attrs.get("units")

    return xasmapdata


def _get_scan_end_reason(nxentry: h5py.Group) -> Optional[str]:
    if "end_reason" not in nxentry:
        return
    end_reason = nxentry["end_reason"][()]
    if isinstance(end_reason, bytes):
        end_reason = end_reason.decode()
    return end_reason


def _parse_single_xas_data(
    energy_data: numpy.ndarray,
    mu_data: numpy.ndarray,
    x0_data: numpy.ndarray,
    x1_data: numpy.ndarray,
) -> _AccumulateData:
    nenergy = min(len(energy_data), len(mu_data))
    x0_data = x0_data[0]
    x1_data = x1_data[0]
    return _AccumulateData(
        mu=[mu_data[:nenergy]],
        energy=[energy_data[:nenergy]],
        x0=[x0_data],
        x1=[x1_data],
    )


def _parse_multi_xas_data(
    energy_data: numpy.ndarray,
    mu_data: numpy.ndarray,
    x0_data: numpy.ndarray,
    x1_data: numpy.ndarray,
) -> _AccumulateData:
    npts, nenergy = mu_data.shape
    if energy_data.ndim == 1:
        # Shape (nenergy,) -> (npts, nenergy)
        energy_data = numpy.tile(energy_data, (npts, 1))
    nenergy = min(nenergy, energy_data.shape[1])
    npts = min(len(mu_data), len(energy_data), len(x0_data), len(x1_data))
    return _AccumulateData(
        mu=mu_data[:npts, :nenergy].tolist(),
        energy=energy_data[:npts, :nenergy].tolist(),
        x0=x0_data[:npts].tolist(),
        x1=x1_data[:npts].tolist(),
    )


def _extract_data(dataset: h5py.Dataset) -> numpy.ndarray:
    """The shape to the returned dataset is 1D or 2D."""
    if dataset.ndim == 0:
        return numpy.array([dataset[()]])
    elif dataset.ndim == 1:
        return dataset[()]
    elif dataset.ndim == 2:
        if dataset.shape[0] == 1:
            return dataset[0]
        else:
            return dataset[()]
    else:
        raise ValueError(
            f"Dataset has {dataset.ndim} dimensions which is not supported ({dataset.file.filename}::{dataset.name})"
        )
