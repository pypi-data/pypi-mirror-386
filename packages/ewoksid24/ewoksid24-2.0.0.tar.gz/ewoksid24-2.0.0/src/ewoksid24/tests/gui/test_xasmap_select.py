import os

from silx.gui import qt

from ...gui.xasmap_select import XasMapInputWidget


def test_add_xasmap(qtbot):
    fake_files = ["/tmp/file1.h5", "/tmp/file2.h5"]
    widget = XasMapInputWidget()
    widget.add_xasmap(
        filenames=fake_files,
        dim0_counter="x",
        dim1_counter="y",
        energy_counter="energy",
        mu_counter="mu",
        scan_ranges="[[1, 5]]",
        exclude_scans="[[2, 3]]",
    )
    qtbot.addWidget(widget)

    xasmaps = widget._get_xasmaps()
    assert len(xasmaps) == 1

    xasmap = xasmaps[0]
    assert xasmap["filenames"] == list(map(os.path.realpath, fake_files))
    assert xasmap["dim0_counter"] == "x"
    assert xasmap["dim1_counter"] == "y"
    assert xasmap["energy_counter"] == "energy"
    assert xasmap["mu_counter"] == "mu"
    assert xasmap["scan_ranges"] == [[1, 5]]
    assert xasmap["exclude_scans"] == [[2, 3]]


def test_invalid_scan_range_warns(monkeypatch):
    widget = XasMapInputWidget()
    widget.add_xasmap(
        filenames=["/tmp/file1.h5"],
        dim0_counter="x",
        dim1_counter="y",
        energy_counter="energy",
        mu_counter="mu",
    )
    assert len(widget._get_xasmaps()) == 1

    widget._scan_range_input.setText("[[1]]")  # Invalid scan range (only one value)

    called = False

    def fake_warning(*args, **kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr(qt.QMessageBox, "warning", fake_warning)

    widget._create_xasmap()

    assert called is True
    assert len(widget._get_xasmaps()) == 1
