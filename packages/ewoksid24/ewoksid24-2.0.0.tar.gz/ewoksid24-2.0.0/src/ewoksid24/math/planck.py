import logging
from typing import Optional

import numpy
import scipy.constants
from scipy.optimize import curve_fit

from ..io.temperature import TemperatureData

_logger = logging.getLogger(__name__)


def spectral_radiance(wavelength: numpy.ndarray, temperature: float, scale: float):
    r"""Planck's law describing the spectral density of electromagnetic radiation emitted by
    a black body in thermal equilibrium at a given temperature T.

    .. math::

        B(\lambda, T) = \frac{2hc^2}{\lambda^5} \cdot \frac{1}{e^{\frac{hc}{\lambda kT} - 1}}

    Where:

    - :math:`B(\lambda, T)` is the spectral radiance (:math:`\frac{W}{m^3\text{sr}}`) at wavelength :math:`\lambda` and temperature :math:`T`.
    - :math:`h` is Planck's constant (:math:`6.62607015 \times 10^{-34}` J·s).
    - :math:`c` is the speed of light in vacuum (:math:`2.998 \times 10^8` m/s).
    - :math:`k` is the Boltzmann constant (:math:`1.380649 \times 10^{-23}` J/K).
    - :math:`\lambda` is the wavelength of the radiation in meters.
    - :math:`T` is the temperature of the blackbody radiator in Kelvin.

    :param wavelength: wavelength in nanometer
    :param temperature: temperature in Kelvin
    :param scale: scaling factor to fit the data
    :returns: spectral radiance
    """
    h = scipy.constants.Planck  # J·s
    c = scipy.constants.speed_of_light  # m/s
    k = scipy.constants.Boltzmann  # J/K

    lam = wavelength * 1e-9
    exp = numpy.exp((h * c) / (lam * k * temperature))
    radiance = (2 * h * c**2) / (lam**5) / (exp - 1)
    return radiance * scale


def fit_temperature_data(
    temp_data: TemperatureData,
    wavelength_min: Optional[float] = None,
    wavelength_max: Optional[float] = None,
) -> None:
    """Fit temperature data and overwrite the existing fit results."""
    yfit = numpy.zeros(temp_data.planck_fit.shape[1], dtype=temp_data.planck_fit.dtype)

    xyiter = zip(temp_data.wavelength, temp_data.planck_data)
    for i, (x, y) in enumerate(xyiter):
        if wavelength_min is None:
            start = temp_data.planck_fit_slice.start
        else:
            start = numpy.argmin(numpy.abs(x - wavelength_min))
        if wavelength_max is None:
            stop = temp_data.planck_fit_slice.stop
        else:
            stop = numpy.argmin(numpy.abs(x - wavelength_max)) + 1
        fit_slice = slice(start, stop)
        temp_data.planck_fit_slice = fit_slice
        x = x[fit_slice]
        y = y[fit_slice]

        temperature0 = temp_data.planck_temperature[i]
        scale0 = numpy.median(y / spectral_radiance(x, temperature0, 1))
        p0 = [temperature0, scale0]

        (temperature, scale), _ = curve_fit(spectral_radiance, x, y, p0=p0)

        yfit[fit_slice] = spectral_radiance(x, temperature, scale)
        temp_data.planck_fit[i] = yfit

        _logger.debug(
            "Point %d: %f K -> %f K", i, temp_data.planck_temperature[i], temperature
        )
        temp_data.planck_temperature[i] = temperature
