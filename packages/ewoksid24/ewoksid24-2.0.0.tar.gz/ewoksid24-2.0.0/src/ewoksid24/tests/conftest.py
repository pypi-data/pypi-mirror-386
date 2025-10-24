import os

import h5py
import numpy
import pytest

from .data import RESOURCE_ROOT


@pytest.fixture
def xanes_filename():
    return os.path.join(RESOURCE_ROOT, "xanes.h5")


@pytest.fixture
def id24_dcm_xasmap(tmp_path):
    x = numpy.linspace(-1, 2, 10)
    y = numpy.linspace(3, 2, 9)

    xv, yv = numpy.meshgrid(x, y)
    xv = xv.flatten()
    yv = yv.flatten()

    energy = numpy.linspace(7, 7.1, 20)
    mu = numpy.linspace(0, 1, 20)

    filename = str(tmp_path / "id24_dcm.h5")
    with h5py.File(filename, "w") as nxroot:
        for i in range(len(xv)):
            nxroot[f"/{i}.1/instrument/positioners/x"] = xv[i]
            nxroot[f"/{i}.1/instrument/positioners/x"].attrs["units"] = "um"
            nxroot[f"/{i}.1/instrument/positioners/y"] = yv[i]
            nxroot[f"/{i}.1/instrument/positioners/y"].attrs["units"] = "um"
            nxroot[f"/{i}.1/measurement/energy"] = energy
            nxroot[f"/{i}.1/measurement/energy"].attrs["units"] = "keV"
            nxroot[f"/{i}.1/measurement/mu"] = mu + 0.01 * i

    return {
        "filenames": [filename],
        "dim0_counter": "x",
        "dim1_counter": "y",
        "mu_counter": "mu",
        "energy_counter": "energy",
    }


@pytest.fixture
def id24_ed_xasmap(tmp_path):
    x = numpy.linspace(-1, 2, 10)
    y = numpy.linspace(3, 2, 9)

    xv, yv = numpy.meshgrid(x, y)
    xv = xv.flatten()
    yv = yv.flatten()

    energy = numpy.linspace(7, 7.1, 20)[None, :]
    mu = numpy.linspace(0, 1, 20)
    mu = numpy.arange(len(xv))[:, None] * mu[None, :]

    filename = str(tmp_path / "id24_ed.h5")
    with h5py.File(filename, "w") as nxroot:
        nxroot["/1.1/instrument/positioners/x"] = xv
        nxroot["/1.1/instrument/positioners/x"].attrs["units"] = "um"
        nxroot["/1.1/instrument/positioners/y"] = yv
        nxroot["/1.1/instrument/positioners/y"].attrs["units"] = "um"
        nxroot["/1.1/measurement/energy"] = energy
        nxroot["/1.1/measurement/energy"].attrs["units"] = "keV"
        nxroot["/1.1/measurement/mu"] = mu

    return {
        "filenames": [filename],
        "dim0_counter": "x",
        "dim1_counter": "y",
        "mu_counter": "mu",
        "energy_counter": "energy",
    }
