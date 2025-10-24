from silx.gui import qt

from ...gui.xasmap_viewer import XasMapViewer


def test_viewer_initializes(qtbot):
    widget = XasMapViewer()
    qtbot.addWidget(widget)
    widget.show()

    assert widget.windowTitle() == "XAS Map Viewer"
    assert isinstance(widget._plot2d_widget, qt.QWidget)
    assert widget._function_dropdown.count() > 0


def test_add_xasmap(qtbot, qapp, id24_dcm_xasmap):
    widget = XasMapViewer()
    qtbot.addWidget(widget)

    widget.show()

    with qtbot.waitSignal(widget.plot_updated, timeout=30000):
        widget.add_xasmap(
            filenames=id24_dcm_xasmap["filenames"],
            dim0_counter=id24_dcm_xasmap["dim0_counter"],
            dim1_counter=id24_dcm_xasmap["dim1_counter"],
            energy_counter=id24_dcm_xasmap["energy_counter"],
            mu_counter=id24_dcm_xasmap["mu_counter"],
        )

    images = widget._plot2d_widget.getAllImages()
    curves = widget._plot1d_widget.getAllCurves()

    assert len(images) == 1
    assert len(curves) == 1

    assert images[0].getName() == "Sum of μ"
    assert curves[0].getName() == "μ"

    qapp.processEvents()
