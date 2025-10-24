import matplotlib.pyplot as plt
import numpy

from ..io.temperature import TemperatureData
from ..io.xas import XasData


def plot_xas(
    xas_data: XasData,
    temp_up_data: TemperatureData,
    temp_down_data: TemperatureData,
    title: str,
    figsize=None,
) -> None:
    epoch_min = min(
        [min(xas_data.epoch), min(temp_up_data.epoch), min(temp_down_data.epoch)]
    )

    fig, ax1 = plt.subplots(figsize=figsize)
    fig.suptitle(title)
    xas_color = "k"
    ax1.plot(xas_data.epoch - epoch_min, xas_data.mu, color=xas_color)
    ax1.set_xlabel("time (sec)")
    ax1.set_ylabel("mu", color=xas_color)
    ax1.tick_params(axis="y", labelcolor=xas_color)

    ax2 = ax1.twinx()
    temp_color = "tab:red"
    ax2.set_ylabel("Temperature (K)", color=temp_color)

    temp_up_avg = numpy.average(temp_up_data.planck_temperature)
    ax2.plot(
        temp_up_data.epoch - epoch_min,
        temp_up_data.planck_temperature,
        "-o",
        color="green",
        label=f"<{temp_up_data.label}> = {temp_up_avg:.0f} K",
    )

    temp_ds_avg = numpy.average(temp_down_data.planck_temperature)
    ax2.plot(
        temp_down_data.epoch - epoch_min,
        temp_down_data.planck_temperature,
        "-o",
        color="blue",
        label=f"<{temp_down_data.label}> = {temp_ds_avg:.0f} K",
    )
    ax2.tick_params(axis="y", labelcolor=temp_color)
    ax2.legend()

    fig.tight_layout()
