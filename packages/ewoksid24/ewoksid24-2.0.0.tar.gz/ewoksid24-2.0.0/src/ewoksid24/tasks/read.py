from ewokscore import Task

from ..io.temperature import read_temperature_data
from ..io.xas import read_xas_data


class ScanTemperatureRead(
    Task,
    input_names=["filename", "scan_number"],
    optional_input_names=["subscan_number", "retry_timeout", "retry_period"],
    output_names=["temp_up_data", "temp_down_data"],
):
    """Read laser-heated DAC scan with temperature data."""

    def run(self):
        filename = self.inputs.filename
        scan_number = self.inputs.scan_number
        subscan_number = self.get_input_value("subscan_number", 2)
        retry_options = self._get_retry_options()

        self.outputs.temp_up_data = read_temperature_data(
            filename, scan_number, subscan_number, "up", "T_US", **retry_options
        )
        self.outputs.temp_down_data = read_temperature_data(
            filename, scan_number, subscan_number, "down", "T_DS", **retry_options
        )

    def _get_retry_options(self) -> dict:
        return {
            "retry_timeout": self.get_input_value("retry_timeout", 60),
            "retry_period": self.get_input_value("retry_period", 0.5),
        }


class XasTemperatureRead(
    ScanTemperatureRead,
    optional_input_names=["energy_name", "mu_name"],
    output_names=["xas_data"],
):
    """Read laser-heated DAC XAS scan with temperature data."""

    def run(self):
        filename = self.inputs.filename
        scan_number = self.inputs.scan_number
        retry_options = self._get_retry_options()

        energy_name = self.get_input_value("energy_name", "energy_enc")
        mu_name = self.get_input_value("mu_name", "mu_trans")
        self.outputs.xas_data = read_xas_data(
            filename, scan_number, energy_name, mu_name, **retry_options
        )

        super().run()
