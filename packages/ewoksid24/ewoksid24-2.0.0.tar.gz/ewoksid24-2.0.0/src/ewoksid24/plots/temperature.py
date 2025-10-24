from typing import Optional

import matplotlib.pyplot as plt
import numpy

from ..io.temperature import TemperatureData


def plot_temperature(
    temp_up_data: TemperatureData,
    temp_down_data: TemperatureData,
    index: int,
    title: str,
    extend_plotrange_left: Optional[float] = None,
    extend_plotrange_right: Optional[float] = None,
    two_color_difference: Optional[float] = None,
    figsize=None,
):
    """
    :param temp_up_data:
    :param temp_down_data:
    :param index: point index in the scan
    :param title: plot title
    :param extend_plotrange_left: extend the plot range with respect to the fit range on the left in nm
    :param extend_plotrange_right: extend the plot range with respect to the fit range on the right in nm
    :param two_color_difference: compare wavelengths with this difference
    :param figsize: plot size
    """
    if extend_plotrange_left is None:
        extend_plotrange_left = -15  # nm
    if extend_plotrange_right is None:
        extend_plotrange_right = 50  # nm
    if two_color_difference is None:
        two_color_difference = 42  # nm
    fig, ax = plt.subplots(nrows=3, ncols=2, sharex=True, figsize=figsize)
    try:
        fig.suptitle(title)
        _plot_column(
            0,
            ax,
            temp_up_data,
            index,
            extend_plotrange_left,
            extend_plotrange_right,
            two_color_difference,
        )
        _plot_column(
            1,
            ax,
            temp_down_data,
            index,
            extend_plotrange_left,
            extend_plotrange_right,
            two_color_difference,
        )
        fig.tight_layout()
    except Exception:
        plt.close()
        raise


def _plot_column(
    column: int,
    ax: plt.Axes,
    temp_data: TemperatureData,
    index: int,
    extend_plotrange_left: float,
    extend_plotrange_right: float,
    two_color_difference: float,
):
    fit_slice = temp_data.planck_fit_slice

    wavelength = temp_data.wavelength[index]
    response = temp_data.response[index]
    planck_data = temp_data.planck_data[index]
    planck_fit = temp_data.planck_fit[index, fit_slice]
    title = f"{temp_data.label} = {temp_data.planck_temperature[index]:.0f} K"

    # Fit and plot range
    imin = fit_slice.start
    imax = fit_slice.stop - 1
    wavelength_fit_min = wavelength[imin]
    wavelength_fit_max = wavelength[imax]
    xmin = wavelength_fit_min + extend_plotrange_left
    xmax = wavelength_fit_max + extend_plotrange_right

    # Raw data
    ax[0, column].set_title(title)
    ax[0, column].plot(wavelength, response)
    ax[0, column].set_xlim(xmin, xmax)

    # Planck fit
    ax[1, column].plot(wavelength, planck_data)
    ax[1, column].plot(wavelength[fit_slice], planck_fit)
    ax[1, column].set_xlim(xmin, xmax)
    ax[1, column].set_ylim(0, 1.1 * max(planck_data[fit_slice]))

    # Two-color difference
    if not two_color_difference:
        two_color_difference = 0.1 * (wavelength_fit_max - wavelength_fit_min)
    dwavelength = numpy.median(numpy.diff(wavelength))
    d = max(int(two_color_difference / dwavelength), 1)
    diff_start = imin
    diff_stop = min(imax + d + 1, len(wavelength))
    d = diff_stop - imax - 1
    diff_slice = slice(diff_start, diff_stop)

    x = wavelength[diff_slice]
    y = numpy.log(planck_data[diff_slice] / x**5)
    num = y[:-d] - y[d:]
    denom = 1e9 / x[:-d] - 1e9 / x[d:]
    temp_col = num / denom

    ax[2, column].plot(x[:-d], temp_col)
    ax[2, column].set(xlabel="wavelength (nm)")
    ax[2, column].set_xlim(xmin, xmax)
