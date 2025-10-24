from copy import deepcopy

from ewokscore import Task

from ..math.planck import fit_temperature_data


class PlanckRadianceFit(
    Task,
    input_names=["temp_data"],
    optional_input_names=["wavelength_min", "wavelength_max"],
    output_names=["temp_data"],
):
    """Fit Black Body radiance with Planck's law."""

    def run(self):
        temp_data = deepcopy(self.inputs.temp_data)
        wavelength_min = self.get_input_value("wavelength_min", None)
        wavelength_max = self.get_input_value("wavelength_max", None)
        fit_temperature_data(
            temp_data, wavelength_min=wavelength_min, wavelength_max=wavelength_max
        )
        self.outputs.temp_data = temp_data
