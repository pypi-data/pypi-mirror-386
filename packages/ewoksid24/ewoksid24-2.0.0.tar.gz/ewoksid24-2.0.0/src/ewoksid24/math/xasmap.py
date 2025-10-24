from typing import Callable
from typing import Tuple

import numpy
from ewoksfluo.math.regular_grid import ScatterDataInterpolator
from scipy.interpolate import interp1d

from ..io.xasmap import XasMapData


class XasMapInterpolator:

    def __init__(self, data: XasMapData) -> None:
        self._energy_units = data.energy_units
        if data.energy.ndim == 2:
            self._energy_axis, self._mu = interpolate_energy(data)
        elif data.energy.ndim == 1:
            self._energy_axis = data.energy
            self._mu = data.mu
        else:
            raise ValueError("energy field must be 1D or 2D")
        self._interpolator = ScatterDataInterpolator(
            [data.x0, data.x1],
            [data.x0_name, data.x1_name],
            [data.x0_units, data.x1_units],
        )

    @property
    def energy_axis(self):
        return self._energy_axis

    @property
    def energy_label(self) -> str:
        name = "Energy"
        units = self._energy_units
        if units:
            return f"{name} ({units})"
        else:
            return name

    @property
    def x0_axis(self) -> numpy.ndarray:
        return self._interpolator.grid_axes[0]

    @property
    def x1_axis(self) -> numpy.ndarray:
        return self._interpolator.grid_axes[1]

    @property
    def x0_axis_name(self) -> str:
        return self._interpolator.axes_names[0]

    @property
    def x1_axis_name(self) -> str:
        return self._interpolator.axes_names[1]

    @property
    def x0_axis_label(self) -> str:
        return self._axis_label(0)

    @property
    def x1_axis_label(self) -> str:
        return self._axis_label(1)

    @property
    def mu(self):
        return self._mu

    def _axis_label(self, i: int) -> str:
        name = self._interpolator.axes_names[i]
        units = self._interpolator.units
        if units:
            return f"{name} ({units})"
        else:
            return name

    def evaluate_as_map(
        self, xas_func: Callable[[numpy.ndarray, numpy.ndarray], float]
    ) -> numpy.ndarray:
        energy = self.energy_axis
        values = numpy.array([xas_func(energy, mu) for mu in self._mu])
        return self._interpolator.regrid(values)

    def get_single_point_mu(
        self, pos_x0: float, pos_x1: float
    ) -> Tuple[float, float, numpy.ndarray]:
        scatter0, scatter1 = self._interpolator.scatter_coordinates.T
        distance = numpy.abs(scatter0 - pos_x0) + numpy.abs(scatter1 - pos_x1)
        idx = numpy.argmin(distance)
        return scatter0[idx], scatter1[idx], self._mu[idx]


def interpolate_energy(data: XasMapData) -> Tuple[numpy.ndarray, numpy.ndarray]:
    """
    Interpolates all mu spectra to a common energy axis.

    :param data: Input XasMapData with possibly different energy axes per point.
    :returns: Shared energy axis and interpolated mu.
    """
    e0 = data.energy[:, 0].max()
    e1 = data.energy[:, -1].min()
    en = data.energy.shape[1]
    energy = numpy.linspace(e0, e1, en)

    mu_interp = numpy.empty((data.mu.shape[0], len(energy)))
    for i in range(data.mu.shape[0]):
        interp = interp1d(
            data.energy[i], data.mu[i], bounds_error=False, fill_value=numpy.nan
        )
        mu_interp[i] = interp(energy)

    return energy, mu_interp
