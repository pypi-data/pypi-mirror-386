import numpy

from ..io.temperature import read_temperature_data
from ..math import planck


def test_fit_temperature_data(xanes_filename):
    temp_data = read_temperature_data(xanes_filename, 39, 2, "up", "T_US")
    temperature0 = temp_data.planck_temperature.copy()
    planck.fit_temperature_data(temp_data)
    temperature1 = temp_data.planck_temperature.copy()

    # Test: changed but close
    numpy.testing.assert_raises(
        AssertionError, numpy.testing.assert_array_equal, temperature0, temperature1
    )
    numpy.testing.assert_allclose(temperature0, temperature1, atol=1e-3)
