from ..io.xasmap import XasMapData
from ..io.xasmap import read_xasmap
from ..math.xasmap import XasMapInterpolator


def test_xasmap_id24_dcm(id24_dcm_xasmap):
    xasmap = read_xasmap(**id24_dcm_xasmap)
    _assert_xasmap(xasmap)


def test_xasmap_id24_ed(id24_ed_xasmap):
    xasmap = read_xasmap(**id24_ed_xasmap)
    _assert_xasmap(xasmap)


def _assert_xasmap(xasmap: XasMapData):
    assert xasmap.energy_units == "keV"
    assert xasmap.x0_units == "um"
    assert xasmap.x1_units == "um"


def test_xasmap_interpolator(id24_dcm_xasmap):
    xasmap = read_xasmap(**id24_dcm_xasmap)
    interpolator = XasMapInterpolator(xasmap)
    assert interpolator.energy_label == "Energy (keV)"
    assert interpolator.x0_axis_label == "x (um)"
    assert interpolator.x1_axis_label == "y (um)"
