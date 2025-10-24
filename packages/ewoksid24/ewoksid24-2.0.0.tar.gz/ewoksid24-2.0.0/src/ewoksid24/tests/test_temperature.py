import os

import numpy
import pytest
from ewokscore import execute_graph


@pytest.mark.parametrize("with_xas", [True, False])
def test_scan_saving(xanes_filename, tmp_path, with_xas):
    if with_xas:
        read_task = "ewoksid24.tasks.read.XasTemperatureRead"
        plot_task = "ewoksid24.tasks.plot.XasTemperaturePlot"
        nplots = 5
    else:
        read_task = "ewoksid24.tasks.read.ScanTemperatureRead"
        plot_task = "ewoksid24.tasks.plot.ScanTemperaturePlot"
        nplots = 4

    workflow = {
        "graph": {"id": "test_temperature_task"},
        "nodes": [
            {
                "id": 0,
                "task_identifier": read_task,
                "task_type": "class",
                "default_inputs": [
                    {"name": "filename", "value": xanes_filename},
                    {"name": "scan_number", "value": 39},
                    {"name": "retry_timeout", "value": 0},
                ],
            },
            {
                "id": 1,
                "task_identifier": plot_task,
                "task_type": "class",
                "default_inputs": [
                    {"name": "output_directory", "value": str(tmp_path)}
                ],
            },
        ],
        "links": [{"source": 0, "target": 1, "map_all_data": True}],
    }

    result = execute_graph(workflow)

    filenames = result["filenames"]
    assert len(filenames) == nplots
    for filename in filenames:
        assert filename.endswith(".png")
        assert os.path.isfile(filename)


@pytest.mark.parametrize("with_xas", [True, False])
def test_fitting(xanes_filename, with_xas):
    if with_xas:
        read_task = "ewoksid24.tasks.read.XasTemperatureRead"
    else:
        read_task = "ewoksid24.tasks.read.ScanTemperatureRead"

    workflow = {
        "graph": {"id": "test_temperature_task"},
        "nodes": [
            {
                "id": 0,
                "task_identifier": read_task,
                "task_type": "class",
                "default_inputs": [
                    {"name": "filename", "value": xanes_filename},
                    {"name": "scan_number", "value": 39},
                    {"name": "retry_timeout", "value": 0},
                ],
            },
            {
                "id": 1,
                "task_identifier": "ewoksid24.tasks.fit.PlanckRadianceFit",
                "task_type": "class",
            },
        ],
        "links": [
            {
                "source": 0,
                "target": 1,
                "data_mapping": [
                    {"source_output": "temp_up_data", "target_input": "temp_data"}
                ],
            }
        ],
    }

    result = execute_graph(
        workflow,
        outputs=[{"id": 0, "name": "temp_up_data"}, {"id": 1, "name": "temp_data"}],
    )

    temperature0 = result["temp_up_data"].planck_temperature
    temperature1 = result["temp_data"].planck_temperature

    # Test: changed but close
    numpy.testing.assert_raises(
        AssertionError, numpy.testing.assert_array_equal, temperature0, temperature1
    )
    numpy.testing.assert_allclose(temperature0, temperature1, atol=1e-3)
