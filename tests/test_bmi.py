import json

import numpy as np
import pytest
import yaml

from waterledger_models.datacenter import physics as model
from waterledger_models.datacenter.bmi import CoolingWaterBmi
from waterledger_models.datacenter.bmi import INPUTS, OUTPUTS
from test_physics_properties import synthetic_weather

TEMP = "atmosphere_bottom_air__temperature"
RH = "atmosphere_bottom_air_water_vapor__relative_saturation"
WITHDRAWN = "data_center_cooling_water__withdrawal_volume_flux"
CONSUMED = "data_center_cooling_water__consumption_volume_flux"
RETURNED = "data_center_cooling_water__return_volume_flux"


def write_config(tmp_path, **cfg):
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(cfg))
    return str(path)


def test_information_and_variables(tmp_path):
    m = CoolingWaterBmi()
    m.initialize(write_config(tmp_path, design="towers", it_capacity_mw=100))
    assert m.get_component_name()
    assert m.get_input_item_count() == len(m.get_input_var_names()) == 4
    assert m.get_output_item_count() == len(m.get_output_var_names()) == 6
    for name in list(INPUTS) + list(OUTPUTS):
        assert m.get_var_grid(name) == 0
        assert m.get_var_type(name) == "float64"
        assert m.get_var_itemsize(name) == 8 and m.get_var_nbytes(name) == 8
        assert m.get_var_location(name) == "node"
        assert m.get_var_units(name)
    assert m.get_grid_type(0) == "scalar" and m.get_grid_rank(0) == 0 and m.get_grid_size(0) == 1
    assert m.get_time_units() == "s" and m.get_time_step() == 3600 and m.get_start_time() == 0
    with pytest.raises(NotImplementedError):
        m.get_grid_shape(0, np.empty(0, dtype=int))
    m.finalize()


def test_set_value_drives_the_model(tmp_path):
    m = CoolingWaterBmi()
    m.initialize(write_config(tmp_path, design="towers", it_capacity_mw=100))
    out = np.empty(1)
    m.set_value(TEMP, np.array([30.0]))
    m.set_value(RH, np.array([50.0]))
    hot = m.get_value(WITHDRAWN, out).copy()
    m.set_value(TEMP, np.array([0.0]))
    cold = m.get_value(WITHDRAWN, out).copy()
    assert hot > cold > 0
    w, c, r = (m.get_value(n, np.empty(1))[0] for n in (WITHDRAWN, CONSUMED, RETURNED))
    n = m.get_value("data_center_cooling_water__condensate_volume_flux", np.empty(1))[0]
    assert w + n == pytest.approx(c + r, rel=1e-12)
    # matches the model directly: gal per kWh x kWh per second / gal per m3, plus staff water at 100 MW
    p = model.central_parameters()
    gal = model.hourly_rates(np.array([0.0]), model.wet_bulb(np.array([0.0]), 50.0), "towers", p, 50.0)[0][0]
    staff = model.staff_water(model.central_staff(), 100)[0] * 1e6 / 86400 / model.GAL_M3
    assert w == pytest.approx(gal * 100 * 1000 * p["utilization"] / 3600 / model.GAL_M3 + staff, rel=1e-12)
    ptr = m.get_value_ptr(WITHDRAWN)
    m.set_value(TEMP, np.array([25.0]))
    assert ptr[0] == m.get_value(WITHDRAWN, np.empty(1))[0]     # the pointer stays live
    idx = m.get_value_at_indices(TEMP, np.empty(1), np.array([0]))
    assert idx[0] == 25.0
    m.set_value_at_indices(TEMP, np.array([0]), np.array([10.0]))
    assert m.get_value(TEMP, np.empty(1))[0] == 10.0
    with pytest.raises(KeyError):
        m.set_value(WITHDRAWN, np.array([1.0]))


def test_forcing_file_and_update_until(tmp_path):
    time, t, rh = synthetic_weather(10)
    forcing = tmp_path / "weather.json"
    forcing.write_text(json.dumps({"hourly": {"time": [str(x) for x in time.astype("datetime64[m]")],
                                              "temperature_2m": t.tolist(), "relative_humidity_2m": rh.tolist()}}))
    m = CoolingWaterBmi()
    m.initialize(write_config(tmp_path, design="hybrid", it_capacity_mw=50, forcing=str(forcing), parameters={"coc": 4}))
    assert m.get_end_time() == len(t) * 3600
    total = 0.0
    while m.get_current_time() < m.get_end_time():
        total += m.get_value(WITHDRAWN, np.empty(1))[0] * 3600
        m.update()
    p = {**model.for_location(model.central_parameters(), t), "coc": 4.0}
    gal = model.hourly_rates(t, model.wet_bulb(t, rh), "hybrid", p, rh)[0]
    staff = model.staff_water(model.central_staff(), 50)[0] * 1e6 / 24     # gallons an hour
    expected = (gal * 50 * 1000 * p["utilization"] + staff).sum() / model.GAL_M3
    assert total == pytest.approx(expected, rel=1e-9)
    m.initialize(write_config(tmp_path, design="hybrid", forcing=str(forcing)))
    m.update_until(5 * 3600)
    assert m.get_current_time() == 5 * 3600
    assert m.get_value(TEMP, np.empty(1))[0] == pytest.approx(t[5])


def test_closed_loop_includes_staff_water_at_capacity(tmp_path):
    """A 300 MW closed-loop campus: loop top-ups plus staff water for the people on site, as Water Ledger 1.3."""
    m = CoolingWaterBmi()
    m.initialize(write_config(tmp_path, design="dry", it_capacity_mw=300))
    m.set_value(TEMP, np.array([20.0]))
    m.set_value(RH, np.array([60.0]))
    w, c, r = (m.get_value(n, np.empty(1))[0] * 86400 * model.GAL_M3 for n in (WITHDRAWN, CONSUMED, RETURNED))  # gal/day
    topup = 300 * 7000 * 0.03 / 365
    staff, maint = (40 + 0.3 * 300) * 20, 1000 + 11 * 300          # people, and maintenance at the middle of its ranges
    assert w == pytest.approx(topup + staff + maint, rel=1e-9)
    assert c == pytest.approx(topup + 0.1 * staff + 0.09 * maint, rel=1e-9) and w == pytest.approx(c + r, rel=1e-12)
    m.initialize(write_config(tmp_path, design="dry", it_capacity_mw=300, parameters={"staff_gpcd": 30, "topup": 0.01}))
    w2 = m.get_value(WITHDRAWN, np.empty(1))[0] * 86400 * model.GAL_M3
    assert w2 == pytest.approx(300 * 7000 * 0.01 / 365 + 130 * 30 + maint, rel=1e-9)


def test_specific_humidity_and_pressure(tmp_path):
    """NextGen's forcing carries specific humidity and pressure: the component converts them and gives what relative humidity gives."""
    from waterledger_models.weather import specific_humidity
    for design in model.DESIGNS:
        params = {"design_db": 31.0} if design == "hybrid" else {}
        rel, spec = CoolingWaterBmi(), CoolingWaterBmi()
        rel.initialize(write_config(tmp_path, design=design, parameters=params))
        spec.initialize(write_config(tmp_path, design=design, humidity="specific", parameters=params))
        for t, rh, p in ((30.0, 60.0, 98000.0), (5.0, 85.0, 101325.0), (-10.0, 40.0, 95000.0)):
            rel.set_value(TEMP, np.array([t]))
            rel.set_value(RH, np.array([rh]))
            spec.set_value(TEMP, np.array([t]))
            spec.set_value("atmosphere_bottom_air_water_vapor__specific_saturation", np.array([specific_humidity(t, rh, p)]))
            spec.set_value("land_surface_air__pressure", np.array([p]))
            rel.update()
            spec.update()
            for name in OUTPUTS:
                assert spec.get_value(name, np.empty(1))[0] == pytest.approx(rel.get_value(name, np.empty(1))[0], rel=1e-9), (design, name)
            w, c, r, n = (spec.get_value(k, np.empty(1))[0] for k in (WITHDRAWN, CONSUMED, RETURNED, "data_center_cooling_water__condensate_volume_flux"))
            assert w + n == pytest.approx(c + r, rel=1e-12)


def test_configuration_as_a_dict(tmp_path):
    cfg = {"design": "hybrid", "it_capacity_mw": 50, "end_time": 7200, "parameters": {"design_db": 31.0, "coc": 4}}
    from_file, from_dict = CoolingWaterBmi(), CoolingWaterBmi()
    from_file.initialize(write_config(tmp_path, **cfg))
    from_dict.initialize(cfg)
    assert cfg["parameters"] == {"design_db": 31.0, "coc": 4}       # the caller's dict is left as it was
    for m in (from_file, from_dict):
        m.set_value(TEMP, np.array([29.0]))
        m.set_value(RH, np.array([55.0]))
        m.update()
    assert from_dict.get_end_time() == 7200
    for name in OUTPUTS:
        assert from_dict.get_value(name, np.empty(1))[0] == from_file.get_value(name, np.empty(1))[0]
    m = CoolingWaterBmi()
    m.initialize()                                                   # no configuration: towers at 100 MW
    assert m._design == "towers" and m._mw == 100.0


def test_bad_configuration(tmp_path):
    m = CoolingWaterBmi()
    with pytest.raises(ValueError):
        m.initialize(write_config(tmp_path, design="spray-pond"))
    with pytest.raises(ValueError):
        m.initialize(write_config(tmp_path, parameters={"not_a_parameter": 1}))
    with pytest.raises(ValueError):
        m.initialize(write_config(tmp_path, humidity="dew point"))
    with pytest.raises(ValueError):
        m.initialize(write_config(tmp_path, humidity="specific", forcing="weather.json"))


def test_condensate_output_in_humid_air(tmp_path):
    m = CoolingWaterBmi()
    m.initialize(write_config(tmp_path, design="dry"))
    m.set_value(TEMP, np.array([32.0]))
    m.set_value("atmosphere_bottom_air_water_vapor__relative_saturation", np.array([80.0]))
    m.update()
    w, c, r, n = (m.get_value(k, np.empty(1))[0] for k in (WITHDRAWN, CONSUMED, RETURNED, "data_center_cooling_water__condensate_volume_flux"))
    assert n > 0 and w + n == pytest.approx(c + r, rel=1e-12)
    assert "data_center_cooling_water__condensate_volume_flux" in m.get_output_var_names()


def test_a_component_on_the_public_base():
    """A component built on ScalarPointBmi gets every BMI function but initialize(); the old private name still works."""
    from waterledger_models.datacenter import ScalarPointBmi
    from waterledger_models.datacenter.bmi import _ScalarPointBmi, read_config
    assert _ScalarPointBmi is ScalarPointBmi and issubclass(CoolingWaterBmi, ScalarPointBmi)

    class Doubler(ScalarPointBmi):
        INPUTS = {"x": "m"}
        OUTPUTS = {"y": "m"}
        _name = "doubler"

        def initialize(self, config_file=None):
            cfg = read_config(config_file)
            self._dt, self._end, self._time = float(cfg.get("time_step", 60)), float(cfg.get("end_time", 600)), 0.0

        def _compute(self):
            self._values["y"][0] = 2 * self._values["x"][0]

    m = Doubler()
    m.initialize({"time_step": 60})
    ptr = m.get_value_ptr("y")
    m.set_value("x", np.array([1.5]))
    m.update_until(300)
    assert m.get_current_time() == 300 and m.get_end_time() == 600 and m.get_time_step() == 60
    assert ptr[0] == 3.0 and m.get_value("y", np.empty(1))[0] == 3.0
    assert m.get_input_var_names() == ("x",) and m.get_output_var_names() == ("y",) and m.get_component_name() == "doubler"
    assert m.get_grid_type(m.get_var_grid("y")) == "scalar" and m.get_var_type("x") == "float64"
    with pytest.raises(KeyError):
        m.set_value("y", np.array([1.0]))
