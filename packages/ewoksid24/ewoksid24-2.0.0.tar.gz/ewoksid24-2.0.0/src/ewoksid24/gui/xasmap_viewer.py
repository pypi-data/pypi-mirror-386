import logging
from concurrent.futures import CancelledError
from concurrent.futures import Future
from concurrent.futures import ThreadPoolExecutor
from typing import Callable
from typing import Dict
from typing import Optional

import numpy
from silx.gui import icons
from silx.gui import qt
from silx.gui.colors import Colormap
from silx.gui.plot import Plot1D
from silx.gui.plot import Plot2D
from silx.gui.plot.CurvesROIWidget import ROI
from silx.gui.utils import blockSignals
from silx.gui.utils.concurrent import submitToQtMainThread

from ..io.xasmap import XasMapData
from ..io.xasmap import read_xasmap
from ..math.xasmap import XasMapInterpolator
from .settings import get_settings
from .xasmap_select import XasMapInputWidget

_logger = logging.getLogger(__name__)


class XasMapViewer(qt.QMainWindow):
    plot_updated = (
        qt.Signal()
    )  # Emits when data loading and plotting has completed (success or failure)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setWindowTitle("XAS Map Viewer")

        self._settings: Optional[qt.QSettings] = None

        # XAS map selecting
        self._input_widget = XasMapInputWidget()
        self._input_widget.data_changed.connect(self._update_plots)
        self._last_read_future = None
        self._executor = ThreadPoolExecutor(max_workers=1)

        # XAS plotting
        plot_widget = qt.QWidget()
        plot_layout = qt.QVBoxLayout(plot_widget)
        plot_layout.setContentsMargins(0, 0, 0, 0)

        # Selected XAS map for plotting
        self._interpolator: Optional[XasMapInterpolator] = None

        # Plot XAS map energy dimension
        self._plot1d_widget = Plot1D()
        self._roi_widget = self._plot1d_widget.getCurvesRoiWidget()
        self._roi_widget.sigROISignal.connect(self._update_roi)
        self._roi_widget.sigROIWidgetSignal.connect(self._update_roi)

        # Plot XAS map spatial dimensions
        self._plot2d_widget = Plot2D()
        self._plot2d_widget.sigPlotSignal.connect(self._on_plot2d_click)
        plot_layout.addWidget(self._plot2d_widget)

        # XAS map spatial dimensions signal
        self._function_dropdown = qt.QComboBox()
        self._function_dropdown.currentIndexChanged.connect(
            self._on_function_dropdown_index_changed
        )
        self._reset_map_functions()
        plot_layout.addWidget(self._function_dropdown)

        # Bliss command of a point in the XAS map spatial dimensions
        self._bliss_command = qt.QLineEdit()
        self._bliss_command.setReadOnly(True)
        copy_bliss_command_button = qt.QToolButton()
        copy_bliss_command_button.setIcon(icons.getQIcon("edit-copy"))
        copy_bliss_command_button.setToolTip("Copy")
        copy_bliss_command_button.clicked.connect(self._copy_bliss_command_to_clipboard)
        click_layout = qt.QHBoxLayout()
        click_layout.addWidget(self._bliss_command)
        click_layout.addWidget(copy_bliss_command_button)
        plot_layout.addLayout(click_layout)

        # Arrange XAS map selection (left), 2D plot (right) and 1D plot (bottom)
        main_layout = qt.QVBoxLayout()

        splitter1 = qt.QSplitter()
        splitter1.setOrientation(qt.Qt.Horizontal)
        splitter1.addWidget(self._input_widget)
        splitter1.addWidget(plot_widget)

        splitter2 = qt.QSplitter()
        splitter2.setOrientation(qt.Qt.Vertical)
        splitter2.addWidget(splitter1)
        splitter2.addWidget(self._plot1d_widget)

        main_layout.addWidget(splitter2)

        central_widget = qt.QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def _on_function_dropdown_index_changed(self, _):
        self._update_plots()

    def _update_plots(self, xasmap: dict = None):
        """This method is called when the XAS map is updated or the function is changed."""
        if xasmap is None:
            xasmap = self._input_widget.get_current_xasmap()
            if xasmap is None:
                return
        self._start_update_plots(xasmap)

    def _start_update_plots(self, xasmap: dict):
        if self._last_read_future is None:
            qt.QApplication.setOverrideCursor(qt.Qt.WaitCursor)

        log_arg = str(xasmap["filenames"])
        _logger.info("Load XAS map: %s", log_arg)

        future = self._executor.submit(
            read_xasmap,
            xasmap["filenames"],
            dim0_counter=xasmap["dim0_counter"],
            dim1_counter=xasmap["dim1_counter"],
            energy_counter=xasmap["energy_counter"],
            mu_counter=xasmap["mu_counter"],
            scan_ranges=xasmap["scan_ranges"],
            exclude_scans=xasmap["exclude_scans"],
        )
        previous_future = self._last_read_future
        self._last_read_future = future
        if previous_future is not None:
            previous_future.cancel()  # after updating _last_read_future

        def on_done(fut: Future) -> None:
            submitToQtMainThread(self._read_xasmap_done, fut, log_arg)

        future.add_done_callback(on_done)

    def _read_xasmap_done(self, future: Future, log_arg: str):
        try:
            result = future.result()
        except CancelledError:
            _logger.warning("XAS map loading cancelled: %s", log_arg)
            return
        except Exception:
            _logger.exception("XAS map loading failed: %s", log_arg)
            result = None
        else:
            _logger.info("XAS map loaded: %s", log_arg)
        self._plot_xasmap(result)

        if future is self._last_read_future:
            qt.QApplication.restoreOverrideCursor()
            self._last_read_future = None

    def _plot_xasmap(self, data: Optional[XasMapData]):
        self._interpolator = None
        try:
            if data is not None and not data.is_empty():
                self._interpolator = XasMapInterpolator(data)
        except Exception:
            _logger.exception("XAS data cannot be interpolated")
        finally:
            try:
                self._update_plot2d()
                self._update_plot1d()
            finally:
                self.plot_updated.emit()

    def _update_plot2d(self) -> None:
        if self._interpolator is None:
            self._plot2d_widget.clearImages()
            return

        selected_function = self._function_dropdown.currentText()
        img = self._interpolator.evaluate_as_map(self._map_functions[selected_function])

        origin = self._interpolator.x0_axis.min(), self._interpolator.x1_axis.min()
        scale = (
            self._interpolator.x0_axis[1] - self._interpolator.x0_axis[0],
            self._interpolator.x1_axis[1] - self._interpolator.x1_axis[0],
        )
        # Axis values are the center of the pixel.
        # The origin is the left corner of the first pixel.
        origin = origin[0] - scale[0] / 2, origin[1] - scale[1] / 2

        self._plot2d_widget.clearImages()
        title = selected_function
        self._plot2d_widget.setGraphTitle(title)

        self._plot2d_widget.addImage(
            img.T,  # X-axis is dimension 0
            legend=title,
            xlabel=self._interpolator.x0_axis_label,
            ylabel=self._interpolator.x1_axis_label,
            origin=origin,
            scale=scale,
        )

    def _update_plot1d(self) -> None:
        if self._interpolator is None:
            self._plot1d_widget.clearCurves()
            return
        signal = numpy.mean(self._interpolator.mu, axis=0)
        self._plot1d(signal, "Average of μ")

    def _plot1d(self, signal: numpy.ndarray, title: str) -> str:
        if self._interpolator is None:
            return
        self._plot1d_widget.addCurve(self._interpolator.energy_axis, signal, legend="μ")
        self._plot1d_widget.setGraphTitle(title)
        self._plot1d_widget.setGraphXLabel(self._interpolator.energy_label)
        self._plot1d_widget.setGraphYLabel("μ")

    def _reset_map_functions(self) -> None:
        self._map_functions: Dict[
            str, Callable[[numpy.ndarray, numpy.ndarray], float]
        ] = {"Sum of μ": _sum_mu, "Average of μ": _mean_mu}
        for name, roi in self._roi_widget.getRois().items():
            name = f"Sum of μ({name} - bkg)"
            self._map_functions[name] = _generate_sum_roi_mu(roi)
        self._reset_function_dropdown()

    def _reset_function_dropdown(self) -> None:
        with blockSignals(self._function_dropdown):
            current_text = self._function_dropdown.currentText()

            self._function_dropdown.clear()
            for name in self._map_functions:
                self._function_dropdown.addItem(name)

            index = self._function_dropdown.findText(current_text)
            index = max(index, 0)
            self._function_dropdown.setCurrentIndex(index)
            self._on_function_dropdown_index_changed(index)

    def _update_roi(self, _):
        self._reset_map_functions()
        self._update_plot2d()

    def _on_plot2d_click(self, event: dict) -> None:
        if (
            event["event"] == "mouseClicked"
            and event["button"] == "left"
            and self._interpolator is not None
        ):
            # X-axis is dimension 0
            pos_x0 = event["x"]
            pos_x1 = event["y"]
            mot_x0 = self._interpolator.x0_axis_name
            mot_x1 = self._interpolator.x1_axis_name

            command = f"umv({mot_x0}, {pos_x0:.6f}, {mot_x1}, {pos_x1:.6f})"
            self._bliss_command.setText(command)

            clipboard = qt.QApplication.clipboard()
            clipboard.setText(command)

            x, y, signal = self._interpolator.get_single_point_mu(pos_x0, pos_x1)
            self._plot1d(signal, f"μ at {mot_x0} = {x:.6f}, {mot_x1} = {y:.6f}")

    def _copy_bliss_command_to_clipboard(self):
        text = self._bliss_command.text()
        if text:
            clipboard = qt.QApplication.clipboard()
            clipboard.setText(text)

    def closeEvent(self, event):  # noqa N802
        self.save_settings()

    def save_settings(self) -> None:
        if self._settings is None:
            return
        self._save_settings_colormap()
        self._input_widget.save_settings()

    def load_settings(self) -> None:
        if self._settings is None:
            self._settings = get_settings()
        self._load_settings_colormap()
        self._input_widget.load_settings()

    def _save_settings_colormap(self) -> None:
        colormap = self._plot2d_widget.getDefaultColormap()
        self._settings.beginGroup("colormap")
        self._settings.setValue("default", colormap.saveState())
        self._settings.endGroup()

    def _load_settings_colormap(self) -> None:
        colormap = None
        self._settings.beginGroup("colormap")
        byte_array = self._settings.value("default", None)
        if byte_array is not None:
            try:
                colormap = Colormap()
                colormap.restoreState(byte_array)
            except Exception:
                _logger.debug("Failed loading color map", exc_info=True)
        self._settings.endGroup()

        if colormap:
            self._plot2d_widget.setDefaultColormap(colormap)

    def add_xasmap(self, *args, **kwargs) -> None:
        self._input_widget.add_xasmap(*args, **kwargs)


def _generate_sum_roi_mu(
    roi: ROI,
) -> Callable[[numpy.ndarray, numpy.ndarray], float]:
    roi_from = roi.getFrom()
    roi_to = roi.getTo()
    energy0 = min(roi_from, roi_to)
    energy1 = max(roi_from, roi_to)

    def _sum_roi(energy, mu):
        mask = (energy >= energy0) & (energy <= energy1)
        if not mask.any():
            return numpy.nan

        energy_roi = energy[mask]
        mu_roi = mu[mask]

        # Estimate background using linear interpolation between the endpoints
        idx0 = numpy.argmin(numpy.abs(energy - energy0))
        idx1 = numpy.argmin(numpy.abs(energy - energy1))
        e0, e1 = energy[idx0], energy[idx1]
        mu0, mu1 = mu[idx0], mu[idx1]

        # Linear background estimated across ROI
        background = mu0 + (mu1 - mu0) * (energy_roi - e0) / (e1 - e0 + 1e-12)
        corrected_mu = mu_roi - background
        corrected_mu[corrected_mu < 0] = 0

        return numpy.sum(corrected_mu)

    return _sum_roi


def _sum_mu(energy: numpy.ndarray, mu: numpy.ndarray) -> float:
    return numpy.sum(mu)


def _mean_mu(energy: numpy.ndarray, mu: numpy.ndarray) -> float:
    return numpy.mean(mu)
