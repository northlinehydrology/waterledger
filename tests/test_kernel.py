"""The compiled heat balance (kernel.py, model 1.10) against physics.py, the reference: every design in every plant, hour by hour and
through a location's Monte Carlo. physics.py is the model; a change there that isn't made in kernel.py fails here."""
import json
import os

import numpy as np
import pytest

from waterledger_models.datacenter import cooling, kernel, physics as ph

HERE = os.path.dirname(__file__)
_W = json.load(open(os.path.join(HERE, "data", "west_michigan_2023_2024.json")))
TDB = np.array(_W["temperature_2m"], dtype=float)
RH = np.array(_W["relative_humidity_2m"], dtype=float)
TWB = ph.wet_bulb(TDB, RH)
TIMES = [str(t)[:13].replace(" ", "T") + ":00" for t in np.datetime64(_W["start"][:13]) + np.arange(len(TDB)).astype("timedelta64[h]")]


def _loads(p):
    p = ph.for_location(p, TDB)
    return p, {**p, "utilization": float(ph.peak_utilization(p))}


@pytest.mark.parametrize("plant", list(ph.PLANTS))
@pytest.mark.parametrize("design", ph.DESIGNS)
def test_every_hour_agrees_with_physics(plant, design):
    weather = kernel.weather_terms(TDB, TWB)
    for p0 in cooling.sample(8, 7, plant) + [cooling.central(plant)]:
        p, at_peak = _loads(p0)
        for a, b in zip(cooling._hourly_run(TDB, TWB, RH, design, p, at_peak), kernel.hourly_run(TDB, TWB, RH, weather, design, p, at_peak)):
            assert np.allclose(b, a, rtol=1e-12, atol=0.0)


@pytest.mark.parametrize("plant", list(ph.PLANTS))
def test_a_locations_monte_carlo_agrees_with_physics(plant):
    fast = cooling.run_location(TIMES, TDB, RH, n=6, plant=plant)
    ref = cooling.run_location(TIMES, TDB, RH, n=6, plant=plant, compiled=False)
    assert fast.keys() == ref.keys()
    for d in ph.DESIGNS:
        for k, v in ref[d].items():
            if isinstance(v, dict):
                for q, x in v.items():
                    assert fast[d][k][q] == pytest.approx(x, rel=1e-12, abs=0.0), (d, k, q)


def test_the_extreme_hours_agree_too():
    """Bitter cold and dry, hot and humid, and the switch points: the branches a mild record may not reach."""
    t = np.r_[np.linspace(-35.0, 45.0, 161), np.full(20, 22.0)]
    rh = np.r_[np.tile([5.0, 50.0, 99.0], 54)[:161], np.linspace(5, 99, 20)]
    wb = ph.wet_bulb(t, rh)
    weather = kernel.weather_terms(t, wb)
    for plant in ph.PLANTS:
        p, at_peak = _loads({**cooling.central(plant), "oa_cfm_per_mw": 1500.0, "humidify_share": 1.0})
        p["design_db"] = at_peak["design_db"] = 31.0
        for design in ph.DESIGNS:
            for a, b in zip(cooling._hourly_run(t, wb, rh, design, p, at_peak), kernel.hourly_run(t, wb, rh, weather, design, p, at_peak)):
                assert np.allclose(b, a, rtol=1e-12, atol=1e-300), (plant, design)


def test_the_kernel_refuses_what_it_does_not_model():
    p, at_peak = _loads(cooling.central())
    weather = kernel.weather_terms(TDB, TWB)
    with pytest.raises(ValueError, match="water limits"):
        kernel.hourly_run(TDB, TWB, RH, weather, "hybrid", {**p, "wet_frac": 0.5}, at_peak)
    with pytest.raises(ValueError, match="only in utilization"):
        kernel.hourly_run(TDB, TWB, RH, weather, "hybrid", p, {**at_peak, "coc": p["coc"] + 1.0})


def test_every_value_physics_uses_reaches_the_kernel():
    """kernel.FIELDS lists what a load carries; the draws' parameters it reads directly must all be in a draw."""
    p = ph.for_location(cooling.central("warm"), TDB)
    derived = {"q", "air", "kg_s", "room", "crah", "air_water", "switch", "hybrid_full", "low", "high", "cp_glycol", "rho_glycol",
               "design_potential", "design_min", "topup"}
    assert set(kernel.FIELDS) - derived <= set(p)
    assert len(kernel.load_values(p, "hybrid")) == len(kernel.FIELDS)
