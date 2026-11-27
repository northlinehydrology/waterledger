"""The tailings pond (design 0025): its water, heat and dissolved mass close every step; reclaim comes before makeup; the tailings lock
water in their pores and fill the impoundment; under a limit the mill processes only the ore its water allows; water above the operating
capacity is released, or held to the crest with zero discharge; its state carries (tests/test_bmi_state.py)."""
import math

import numpy as np
import pytest

from waterledger_models.datacenter import bmi as B
from waterledger_models.ponds import tailings
from waterledger_models.ponds.bmi import (GROUND_MASS, LOCKED_MASS, LW, RAIN, RH, SOLIDS, STORED_MASS, SW, TEMP, WIND,
                                          TailingsPondBmi)

W_ = "water_user_water__withdrawal_volume_flux"
G_ = "water_user_water__gain_volume_flux"
C_ = "water_user_water__consumption_volume_flux"
R_ = "water_user_water__return_volume_flux"
DV = "water_user_water__volume_change_rate"
VOL = "water_user_water__volume"
DEMAND = "water_user_water__demand_volume_flux"
RECLAIM = "water_user_water__reclaim_volume_flux"
UNMET = "water_user_water__unmet_demand_volume_flux"
LOCKED = "water_user_water__entrained_volume_flux"
DEPOSIT = "water_user_tailings__volume"
PROCESSED = "water_user_processed_tailings__mass_flux"
RELEASE = "water_user_water__stream_return_volume_flux"
FREEBOARD = "water_user_water__freeboard_used_volume"
LOST = "water_user__lost_production_time"
SO4 = "dissolved_solids"
MINE = {"capacity_m3": 5e7, "capacity_area_m2": 4e6, "tailings_t_per_day": 50000.0, "initial_pool_m3": 2e6, "initial_temperature": 15.0}
SUMMER = {TEMP: 25.0, RH: 50.0, WIND: 3.5, SW: 280.0, LW: 370.0}


def _mine(**cfg):
    m = TailingsPondBmi()
    m.initialize({**MINE, **cfg})
    return m


def _get(m, k):
    return m.get_value(k, np.empty(1))[0]


def _step(m, **inputs):
    for k, x in inputs.items():
        m.set_value(k, np.array([float(x)]))
    m.update()
    return {k: _get(m, k) for k in m.get_output_var_names()}


def _weather(i):
    """A varied hour: a daily cycle, storms now and then, a seasonal drift."""
    day = i / 24.0
    return {TEMP: 14 + 9 * math.sin(2 * math.pi * (day - 0.375)) + 6 * math.sin(day / 20), RH: 55 + 20 * math.sin(2 * math.pi * day),
            WIND: 1 + 4 * abs(math.sin(i / 7)), SW: max(0.0, 850 * math.sin(2 * math.pi * (day - 0.25))), LW: 320 + 30 * math.sin(day / 9),
            RAIN: 0.006 if i % 131 < 6 else 0.0, B.INTAKE.format(SO4): 0.3 + 0.1 * math.sin(i / 50)}


def test_water_heat_and_mass_close_every_step():
    m = _mine(initial_pool_m3=7e5, min_pool_m3=5e5, catchment_m2=2e6, reclaim_max_m3_s=0.8, initial_concentration={SO4: 2.0},
              solids_release={SO4: 0.05}, parameters={"ore_moisture_m3_t": 0.04, "mill_other_m3_t": 0.08})
    for i in range(24 * 60):
        limit = 0.1 if 600 <= i < 900 else math.inf                  # a drought limit for a while: the mill runs short
        extra = {SOLIDS: 300.0 if 200 <= i < 260 else float("nan")}   # the mill slowed for a few days, then back to its rate
        before = _get(m, STORED_MASS.format(SO4))
        o = _step(m, **_weather(i), **{B.LIMIT: limit}, **extra)
        assert o[W_] + o[G_] == pytest.approx(o[C_] + o[R_] + o[DV], rel=1e-12, abs=1e-12)
        assert o[W_] <= limit * (1 + 1e-12)
        assert o[RECLAIM] + o[W_] + o[UNMET] == pytest.approx(o[DEMAND], rel=1e-12)
        f = m._last
        heat = (f["shortwave"] + f["longwave_in"] - f["longwave_out"] - f["evaporation_heat"] - f["conduction"]
                + f["heat_in_water"] - f["heat_out_water"] + f["freeze_heat"])
        assert f["stored_heat_change"] == pytest.approx(heat, rel=1e-7, abs=1e-2)
        mass_in = f["mass_in"][SO4] * 3600
        assert mass_in == pytest.approx((o[B.RETURN_MASS.format(SO4)] + o[LOCKED_MASS.format(SO4)]) * 3600
                                        + o[STORED_MASS.format(SO4)] - before, rel=1e-9, abs=1e-6)
        assert 0 <= o[GROUND_MASS.format(SO4)] <= o[B.RETURN_MASS.format(SO4)]
    assert o[LOST] > 0


def test_the_tailings_lock_water_in_their_pores():
    p = tailings.TAILINGS_PARAMETERS
    assert tailings.pore_water_m3_t(p) == pytest.approx((2.7 / 1.4 - 1.0) / 2.7)
    m = _mine()
    o = _step(m, **SUMMER)
    solids = 50000.0 / 86400.0
    assert o[LOCKED] == pytest.approx(solids * tailings.pore_water_m3_t(p), rel=1e-12)
    assert o[C_] == pytest.approx(o["water_user_water__evaporation_volume_flux"] + o[LOCKED], rel=1e-12)
    assert o[DEPOSIT] == pytest.approx(solids / 1.4 * 3600, rel=1e-12)
    assert o[PROCESSED] == pytest.approx(solids * 1000, rel=1e-12)


def test_reclaim_comes_before_makeup():
    m = _mine()
    o = _step(m, **SUMMER)
    assert o[DEMAND] == pytest.approx(50000.0 / 86400.0 * (0.65 / 0.35), rel=1e-12)
    assert o[RECLAIM] == pytest.approx(o[DEMAND]) and o[W_] == 0.0
    low = _mine(initial_pool_m3=5e5, min_pool_m3=5e5)               # nothing to reclaim: makeup carries the mill
    o = _step(low, **SUMMER)
    assert o[RECLAIM] == 0.0 and o[W_] == pytest.approx(o[DEMAND])


def test_the_pool_falls_to_its_lowest_workable_volume_and_makeup_takes_over():
    """Reclaim takes the pool down to its lowest volume at the start of a step; the step's free water, less its losses, is there at the end."""
    m = _mine(time_step=86400)
    for _ in range(200):
        before = _get(m, VOL)
        o = _step(m, **SUMMER)
    f = m._last
    assert o[RECLAIM] == pytest.approx((before - 5e5) / 86400, rel=1e-12)
    assert o[VOL] == pytest.approx(5e5 + 86400 * (f["free"] + f["rain"] + f["runoff"] - f["evaporation"] - f["seepage"]), rel=1e-9)
    assert o[VOL] == pytest.approx(before, rel=1e-6)                   # steady
    assert 0 < o[W_] < o[DEMAND]
    assert o[UNMET] == 0.0


def test_under_a_limit_the_mill_processes_only_what_its_water_allows():
    m = _mine(initial_pool_m3=5e5, min_pool_m3=5e5)
    o = _step(m, **SUMMER, **{B.LIMIT: 0.25})
    assert o[W_] == pytest.approx(0.25)
    share = 0.25 / o[DEMAND]
    assert o[UNMET] == pytest.approx(o[DEMAND] - 0.25)
    assert o[PROCESSED] == pytest.approx(50000.0 / 86.4 * share, rel=1e-12)
    assert o[LOST] == pytest.approx(1.0 - share, rel=1e-12)
    dry = _mine(initial_pool_m3=5e5, min_pool_m3=5e5)
    o = _step(dry, **SUMMER, **{B.DRY_MODE: 1.0})
    assert o[W_] == 0.0 and o[PROCESSED] == 0.0 and o[LOST] == pytest.approx(1.0)


def test_water_above_the_operating_capacity_is_released():
    m = _mine(initial_pool_m3=4.9e6, initial_tailings_m3=4.5e7, catchment_m2=2e7, parameters={"pool_depth_m": 1.5})
    o = _step(m, **SUMMER, **{RAIN: 0.02})
    assert o[RELEASE] > 0
    assert o[VOL] + o[DEPOSIT] == pytest.approx(5e7, rel=1e-12)
    assert o[FREEBOARD] == 0.0


def test_zero_discharge_holds_to_the_crest():
    m = _mine(initial_pool_m3=4.9e6, initial_tailings_m3=4.5e7, catchment_m2=2e7, discharge="zero", parameters={"pool_depth_m": 1.5})
    o = _step(m, **SUMMER, **{RAIN: 0.02})
    assert o[RELEASE] == 0.0
    assert o[FREEBOARD] == pytest.approx(o[VOL] + o[DEPOSIT] - 5e7, rel=1e-12) and o[FREEBOARD] > 0
    for _ in range(40):                                          # storm after storm: above the crest it goes
        o = _step(m, **SUMMER, **{RAIN: 0.05})
    assert o[RELEASE] > 0
    assert o[VOL] + o[DEPOSIT] == pytest.approx(5.5e7, rel=1e-12)


def test_the_tailings_fill_the_impoundment():
    m = _mine(capacity_m3=3.1e6, capacity_area_m2=1e6, initial_pool_m3=1e6, time_step=86400)
    with pytest.raises(RuntimeError, match="full"):
        for _ in range(100):
            _step(m, **SUMMER)
    assert _get(m, DEPOSIT) == pytest.approx(int(3.1e6 / (50000 / 1.4)) * 50000 / 1.4, rel=1e-9)


def test_the_solids_rate_can_be_set_each_step():
    m = _mine()
    assert _step(m, **SUMMER, **{SOLIDS: 0.0})[DEMAND] == 0.0           # the mill stopped by a schedule
    assert _step(m, **SUMMER)[DEMAND] == 0.0                            # an input holds until set again
    o = _step(m, **SUMMER, **{SOLIDS: float("nan")})                    # NaN: back to the configured rate
    assert o[PROCESSED] == pytest.approx(50000.0 / 86.4)


def test_the_pool_concentrates_as_it_evaporates():
    m = _mine(initial_concentration={SO4: 1.0}, time_step=86400)
    for _ in range(60):
        o = _step(m, **SUMMER, **{B.INTAKE.format(SO4): 1.0})
    assert o[STORED_MASS.format(SO4)] / o[VOL] > 1.0


@pytest.mark.parametrize("bad, match", [
    ({"capacity_m3": None}, "needs capacity_m3"),
    ({"parameters": {"solids_share": 1.2}}, "solids_share"),
    ({"parameters": {"dry_density_t_m3": 3.0}}, "dry_density"),
    ({"parameters": {"solids_share": 0.9}}, "pores hold more water"),
    ({"parameters": {"nope": 1}}, "unknown parameters"),
    ({"discharge": "sometimes"}, "discharge"),
    ({"initial_tailings_m3": 6e7}, "initial_tailings_m3"),
    ({"initial_pool_m3": 0.0}, "initial_pool_m3"),
    ({"solids_release": {"iron": 1.0}}, "solids_release"),
])
def test_bad_configurations_are_refused(bad, match):
    cfg = {**MINE, **bad}
    cfg = {k: v for k, v in cfg.items() if v is not None}
    with pytest.raises(ValueError, match=match):
        TailingsPondBmi().initialize(cfg)
