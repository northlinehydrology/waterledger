"""The shared heat rejection code (design 0009): data center results are the same as before it moved out of datacenter/physics.py, the data
center model reads the shared equipment ranges rather than copies, and the tower water closes on its own."""
import json
import os

import numpy as np
import pytest

from waterledger_models import heat_rejection as hr
from waterledger_models.datacenter import physics as ph

HERE = os.path.dirname(__file__)
REF = json.load(open(os.path.join(HERE, "data", "datacenter_before_heat_rejection.json")))
_W = json.load(open(os.path.join(HERE, "data", "west_michigan_2023_2024.json")))
TDB = np.array(_W["temperature_2m"], dtype=float)
RH = np.array(_W["relative_humidity_2m"], dtype=float)


@pytest.mark.parametrize("design", ph.DESIGNS)
def test_data_center_results_are_unchanged(design):
    """Hourly water, power and heat at central parameters, exactly as they were before the move (model 1.11)."""
    twb = ph.wet_bulb(TDB, RH)
    p = ph.for_location(ph.central_parameters(), TDB)
    w, c, r = ph.hourly_rates(TDB, twb, design, p, RH)
    power, heat = ph.hourly_heat_power(TDB, twb, design, p, RH)
    hours = REF["hours"]
    for name, got in (("withdrawn", w), ("consumed", c), ("returned", r), ("power", power), ("heat", heat)):
        assert np.ravel(got)[hours].tolist() == REF["designs"][design][name], (design, name)


def test_data_center_reads_the_shared_ranges():
    ranges = {**ph.RANGES, **ph.ADIABATIC, **ph.POWER}
    for k, v in hr.EQUIPMENT.items():
        assert ranges[k] is v, k
    assert ph.wet_bulb is hr.wet_bulb and ph.evaporative_ratio is hr.evaporative_ratio and ph._loop is hr.loop


def test_tower_water_closes():
    """Blowdown and drift carry out the dissolved solids evaporation leaves behind: (blowdown + drift) x (cycles - 1) = evaporation."""
    p = {**{k: (a + b) / 2 for k, (a, b) in hr.EQUIPMENT.items()}, "design_db": hr.design_dry_bulb(TDB)}
    btu = np.full(TDB.shape, hr.KWH_BTU)
    for design in ("towers", "hybrid", "dry"):
        wet = hr.wet_share(TDB, design, p, switch=25.0)
        evap, drift, blow = hr.tower_water(btu, TDB, wet, p)
        assert np.allclose((blow + drift) * (p["coc"] - 1.0), evap, rtol=1e-12, atol=0.0)
        assert (evap >= 0).all() and (evap <= btu / hr.HFG / hr.LB_GAL + 1e-15).all()
    assert not hr.tower_water(btu, TDB, hr.wet_share(TDB, "dry", p, switch=25.0), p)[0].any()


def test_hybrid_switches_on_its_own_setting():
    p = {**{k: (a + b) / 2 for k, (a, b) in hr.EQUIPMENT.items()}, "design_db": 31.0}
    assert hr.switch_point(p, 24.0) == pytest.approx(24.0 + p["switch_margin"])
    assert hr.switch_point(p, 10.0) == hr.SWITCH_SETTINGS[0]               # within the settings controllers allow
    assert hr.switch_point({**p, "switch_on": 26.0}, 20.0) == 26.0
    t = np.array([10.0, 26.0, 40.0])
    s = hr.wet_share(t, "hybrid", p, switch=25.0)
    assert s[0] == 0.0 and 0.0 < s[1] < 1.0 and s[2] == 1.0
