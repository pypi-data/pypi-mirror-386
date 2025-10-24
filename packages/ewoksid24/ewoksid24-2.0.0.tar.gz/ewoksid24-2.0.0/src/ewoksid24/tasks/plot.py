import os
from typing import List

import matplotlib
import matplotlib.pyplot as plt
import numpy
from ewokscore import Task

from ..plots.temperature import plot_temperature
from ..plots.xas import plot_xas


class ScanTemperaturePlot(
    Task,
    input_names=["temp_up_data", "temp_down_data"],
    optional_input_names=[
        "extend_plotrange_left",
        "extend_plotrange_right",
        "two_color_difference",
        "show",
        "pause",
        "output_directory",
        "figsize",
        "dpi",
        "fontsize",
    ],
    output_names=["filenames"],
):
    """Save laser-heated DAC temperature plots as images."""

    def run(self):
        self.prepare()
        self.outputs.filenames = self._plots()

    def _plots(self) -> List[str]:
        return self._temperature_plots(0)

    def _temperature_plots(self, plot_index: int) -> List[str]:
        out_filenames = []

        # Temperature plots
        extend_plotrange_left = self.get_input_value(
            "extend_plotrange_left", None
        )  # nm
        extend_plotrange_right = self.get_input_value(
            "extend_plotrange_right", None
        )  # nm
        two_color_difference = self.get_input_value("two_color_difference", None)  # nm

        filename = self.inputs.temp_up_data.filename
        scan_number = self.inputs.temp_up_data.scan_number
        basename = os.path.basename(self.inputs.temp_up_data.filename)
        dataset = os.path.splitext(basename)[0]
        for index in range(0, len(self.inputs.temp_up_data.epoch)):
            title = f"{dataset} #{scan_number} [{index}]"
            plot_temperature(
                self.inputs.temp_up_data,
                self.inputs.temp_down_data,
                index,
                title,
                extend_plotrange_left=extend_plotrange_left,
                extend_plotrange_right=extend_plotrange_right,
                two_color_difference=two_color_difference,
            )
            try:
                if not self.missing_inputs.output_directory:
                    out_filename = self._get_out_filename(
                        filename, scan_number, index + plot_index
                    )
                    if out_filename:
                        out_filenames.append(out_filename)
                        self.save_plot(out_filename)
                if self.inputs.show:
                    self.show_plot()
            finally:
                plt.close()

        return out_filenames

    def _get_out_filename(self, filename: int, scan_number: int, plotnr: int) -> str:
        output_directory = self.inputs.output_directory
        dataset = os.path.splitext(os.path.basename(filename))[0]
        output_directory = os.path.join(output_directory, dataset, f"scan{scan_number}")
        return os.path.join(output_directory, f"plot{plotnr}.png")

    def prepare(self) -> None:
        if not self.missing_inputs.fontsize:
            matplotlib.rc("font", size=self.inputs.fontsize)

    def save_plot(self, filename: str) -> None:
        path = os.path.dirname(filename)
        if path:
            os.makedirs(path, exist_ok=True)
        plt.gcf().savefig(filename, dpi=self.get_input_value("dpi", 150))

    def show_plot(self) -> None:
        if self.inputs.pause and numpy.isfinite(self.inputs.pause):
            plt.pause(self.inputs.pause)
        else:
            plt.show()


class XasTemperaturePlot(
    ScanTemperaturePlot,
    input_names=["xas_data"],
):
    """Save laser-heated DAC temperature XAS plots as images."""

    def _plots(self) -> List[str]:
        out_filenames = []
        out_filenames += self._xas_plots(len(out_filenames))
        out_filenames += self._temperature_plots(len(out_filenames))
        return out_filenames

    def _xas_plots(self, plot_index: int) -> List[str]:
        filename = self.inputs.xas_data.filename
        scan_number = self.inputs.xas_data.scan_number
        basename = os.path.basename(filename)
        dataset = os.path.splitext(basename)[0]
        title = f"{dataset} #{scan_number}"
        plot_xas(
            self.inputs.xas_data,
            self.inputs.temp_up_data,
            self.inputs.temp_down_data,
            title,
        )
        out_filename = self._get_out_filename(filename, scan_number, plot_index)
        self.save_plot(out_filename)
        return [out_filename]
