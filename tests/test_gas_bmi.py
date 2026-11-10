"""GasPlantBmi (design 0014): each step matches physics.hourly for the same hour, balances close every step, the lake reads its water and wind,
and bad configurations raise."""
import numpy as np
import pytest

from waterledger_models import heat_rejection as hr
from waterledger_models.gas import physics as gp
from waterledger_models.gas.bmi import TO_M3S, WATER, GasPlantBmi

HOURS = [(24.0, 60.0, 500.0), (33.0, 40.0, 650.0), (5.0, 80.0, 200.0)]   # dry-bulb, relative humidity, demand


def _step(m, t, rh, demand, lake_t=None):
    m.set_value("atmosphere_bottom_air__temperature", np.array([t]))
    m.set_value("atmosphere_bottom_air_water_vapor__relative_saturation", np.array([rh]))
    m.set_value("power_plant__electric_power_demand", np.array([demand]))
    if lake_t is not None:
        m.set_value("lake_water_surface__temperature", np.array([lake_t]))
    m.update()
    return {name: m.get_value(name, np.zeros(1))[0] for name in m.get_output_var_names()}


@pytest.mark.parametrize("design", ["towers", "dry", "lake", "hybrid"])
def test_steps_match_the_hourly_physics_and_close(design):
    cfg = {"technology": "cc", "design": design, "units": 2, "unit_mw": 300, "end_time": 3600 * len(HOURS)}
    if design == "hybrid":
        cfg["parameters"] = {"design_db": 31.0}
    m = GasPlantBmi()
    m.initialize(cfg)
    for t, rh, demand in HOURS:
        out = _step(m, t, rh, demand, 12.0 if design == "lake" else None)
        p = {**m._params}
        h = gp.hourly(demand, np.array([t]), hr.wet_bulb(np.array([t]), np.array([rh])), np.array([rh]), "cc", design, p, 2, 300.0,
                      water_t=np.array([12.0]) if design == "lake" else None, discharge=m._discharge)
        for key, name in WATER.items():
            assert out[name] == pytest.approx(h[key][0] * TO_M3S, rel=1e-12, abs=1e-15), (design, key)
        assert out["power_plant__electric_power_output"] == pytest.approx(min(demand, h["capacity"][0]))
        w, c, r = (out[f"water_user_water__{k}_volume_flux"] for k in ("withdrawal", "consumption", "return"))
        assert w == pytest.approx(c + r, rel=1e-12, abs=1e-15)
        assert r == pytest.approx(out["water_user_water__sewer_return_volume_flux"] + out["water_user_water__source_return_volume_flux"]
                                  + out["water_user_water__stream_return_volume_flux"], rel=1e-12, abs=1e-15)


def test_demand_above_capacity_is_unserved():
    m = GasPlantBmi()
    m.initialize({"technology": "ct", "design": "none", "units": 1, "unit_mw": 100, "end_time": 3600})
    out = _step(m, 38.0, 30.0, 150.0)
    assert out["power_plant__electric_power_output"] < 100.0 and out["power_plant__unserved_electric_power"] > 50.0


@pytest.mark.parametrize("cfg", [{"technology": "coal"}, {"technology": "ct", "design": "towers"}, {"technology": "cc", "design": "hybrid"},
                                 {"technology": "engine", "design": "dry", "nox": "water"}, {"parameters": {"bogus": 1.0}},
                                 {"discharge": "river"}, {"supply": "sea"}])
def test_bad_configurations_raise(cfg):
    with pytest.raises(ValueError):
        GasPlantBmi().initialize(cfg)
