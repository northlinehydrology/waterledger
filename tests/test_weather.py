"""Open-Meteo responses load as an xarray Dataset the ensembles and BMI components can read."""
import json

import numpy as np

import pytest

from waterledger_models.datacenter import physics
from waterledger_models.weather import design_dry_bulb, from_open_meteo_json, relative_humidity, saturation_vapor_pressure, specific_humidity
from test_physics_properties import synthetic_weather


def test_reads_a_saved_response(tmp_path):
    payload = {"latitude": 42.9, "longitude": -85.5, "hourly": {"time": ["2024-07-01T00:00", "2024-07-01T01:00"],
                                                                 "temperature_2m": [21.5, 20.9], "relative_humidity_2m": [80, 84]}}
    f = tmp_path / "w.json"
    f.write_text(json.dumps(payload))
    for src in (payload, str(f)):
        ds = from_open_meteo_json(src)
        assert list(ds.air_temperature.values) == [21.5, 20.9] and ds.relative_humidity.attrs["units"] == "%"
        assert ds.time.values[1] - ds.time.values[0] == np.timedelta64(60, "m") and ds.attrs["latitude"] == 42.9


def test_humidity_conversion_round_trips_and_stays_physical():
    t, rh, p = np.meshgrid(np.linspace(-30, 45, 16), np.linspace(0, 100, 21), np.linspace(60000, 105000, 4), indexing="ij")
    q = specific_humidity(t, rh, p)
    assert np.all(q >= 0) and np.all(q <= specific_humidity(t, 100.0, p)) and np.all(q < 1)
    np.testing.assert_allclose(relative_humidity(t, q, p), rh, rtol=1e-12, atol=1e-10)
    # by hand at 20 C, 50%, sea level: es = 611.2 exp(17.67 x 20 / 263.5) = 2337 Pa, e = 1168.5 Pa, q = 0.622 e / (p - 0.378 e)
    assert saturation_vapor_pressure(20.0) == pytest.approx(2337.0, rel=2e-4)
    assert specific_humidity(20.0, 50.0, 101325.0) == pytest.approx(0.622 * 1168.5 / (101325 - 0.378 * 1168.5), rel=2e-4)
    # supersaturated reanalysis air and a negative interpolated q stay within 0-100
    assert relative_humidity(10.0, 2 * specific_humidity(10.0, 100.0, 1e5), 1e5) == 100.0
    assert relative_humidity(10.0, -1e-5, 1e5) == 0.0
    # more water vapor is more humid, warmer air at the same vapor is less
    assert relative_humidity(15.0, 0.008, 1e5) > relative_humidity(15.0, 0.006, 1e5) > relative_humidity(25.0, 0.006, 1e5)


def test_design_dry_bulb_from_any_record(tmp_path):
    """BMI users whose framework supplies the weather get the same design dry-bulb a forcing file gives the component."""
    from waterledger_models.datacenter.bmi import CoolingWaterBmi
    time, t, rh = synthetic_weather(730)
    payload = {"hourly": {"time": [str(x) for x in time.astype("datetime64[m]")], "temperature_2m": t.tolist(), "relative_humidity_2m": rh.tolist()}}
    ds = from_open_meteo_json(payload)
    want = physics.design_dry_bulb(t)
    assert design_dry_bulb(ds) == design_dry_bulb(ds.air_temperature) == design_dry_bulb(t) == design_dry_bulb(list(t)) == want
    assert np.mean(t > want) == pytest.approx(0.004, abs=1 / t.size)
    (tmp_path / "w.json").write_text(json.dumps(payload))
    m = CoolingWaterBmi()
    m.initialize({"design": "hybrid", "forcing": str(tmp_path / "w.json")})
    assert m._params["design_db"] == want
