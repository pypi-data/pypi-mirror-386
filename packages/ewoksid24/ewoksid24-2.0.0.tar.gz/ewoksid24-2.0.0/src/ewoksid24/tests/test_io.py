from ewoksid24.io.temperature import read_temperature_data
from ewoksid24.io.xas import read_xas_data


def test_read_temperature_data(xanes_filename):
    temp_data = read_temperature_data(xanes_filename, 39, 2, "up", "T_US")
    assert temp_data.filename == xanes_filename
    assert temp_data.scan_number == 39

    temp_data = read_temperature_data(xanes_filename, 39, 2, "down", "T_DS")
    assert temp_data.filename == xanes_filename
    assert temp_data.scan_number == 39


def test_read_xas_data(xanes_filename):
    xas_data = read_xas_data(xanes_filename, 39, "energy_enc", "mu_trans")
    assert xas_data.filename == xanes_filename
    assert xas_data.scan_number == 39
