"""The cooling pond (design 0024, part 2): its water, heat and dissolved mass close every step; it holds the cycles of concentration; under a
limit it gives up blowdown, then draws down and warms; below its lowest volume the plant's heat isn't taken; its state carries."""
import math

import numpy as np
import pytest

from waterledger_models.datacenter import bmi as B
from waterledger_models.ponds import physics
from waterledger_models.ponds.bmi import (CoolingPondBmi, GROUND_MASS, HEAT, LW, MAKEUP_T, RAIN, RH, STORED_MASS, SW, TEMP, WIND)

W_ = "water_user_water__withdrawal_volume_flux"
G_ = "water_user_water__gain_volume_flux"
C_ = "water_user_water__consumption_volume_flux"
R_ = "water_user_water__return_volume_flux"
DV = "water_user_water__volume_change_rate"
VOL = "water_user_water__volume"
TP = "water_user_return_water__temperature"
CL = "chloride"
POND = {"area_m2": 4e6, "depth_m": 5.0, "heat_mw": 500.0, "initial_temperature": 20.0}
SUMMER = {TEMP: 25.0, RH: 65.0, WIND: 3.5, SW: 250.0, LW: 380.0}


def _pond(**cfg):
    m = CoolingPondBmi()
    m.initialize({**POND, **cfg})
    return m


def _get(m, k):
    return m.get_value(k, np.empty(1))[0]


def _step(m, **inputs):
    for k, x in inputs.items():
        m.set_value(k, np.array([float(x)]))
    m.update()
    return {k: _get(m, k) for k in m.get_output_var_names()}


def _weather(i):
    """A varied hour: a daily cycle, rain now and then, a seasonal drift."""
    day = i / 24.0
    return {TEMP: 18 + 8 * math.sin(2 * math.pi * (day - 0.375)) + 6 * math.sin(day / 20), RH: 60 + 20 * math.sin(2 * math.pi * day),
            WIND: 1 + 3 * abs(math.sin(i / 7)), SW: max(0.0, 800 * math.sin(2 * math.pi * (day - 0.25))), LW: 330 + 30 * math.sin(day / 9),
            RAIN: 0.004 if i % 97 < 5 else 0.0, B.INTAKE.format(CL): 0.02 + 0.01 * math.sin(i / 50)}


def test_water_heat_and_mass_close_every_step():
    m = _pond(initial_concentration={CL: 0.05})
    for i in range(24 * 40):
        limit = 0.2 if 300 <= i < 500 else math.inf               # a limit for a while, so the pond draws down and refills
        before = _get(m, STORED_MASS.format(CL))
        o = _step(m, **_weather(i), **{B.LIMIT: limit})
        assert o[W_] + o[G_] == pytest.approx(o[C_] + o[R_] + o[DV], rel=1e-12, abs=1e-12)
        assert o[W_] <= limit * (1 + 1e-12)
        f = m._last
        heat_in = (f["heat_in"] + f["shortwave"] + f["longwave_in"] - f["longwave_out"] - f["evaporation_heat"] - f["conduction"]
                   + f["heat_in_water"] - f["heat_out_water"] + f["freeze_heat"])
        assert f["stored_heat_change"] == pytest.approx(heat_in, rel=1e-8, abs=1e-6 * abs(f["heat_in"]))
        mass_in = _get(m, B.INTAKE.format(CL)) * o[W_] * 3600
        assert mass_in == pytest.approx(o[B.RETURN_MASS.format(CL)] * 3600 + o[STORED_MASS.format(CL)] - before, rel=1e-9, abs=1e-9)
        assert 0 <= o[GROUND_MASS.format(CL)] <= o[B.RETURN_MASS.format(CL)]


def test_it_holds_the_cycles_of_concentration():
    """At its steady temperature a pond at the cycles' concentration stays there: blowdown and seepage are evaporation / (cycles - 1)."""
    warm = _pond(heat_mw=300, parameters={"coc": 5.0}, time_step=86400)
    for _ in range(400):
        _step(warm, **SUMMER)
    m = _pond(heat_mw=300, parameters={"coc": 5.0}, time_step=86400, initial_temperature=_get(warm, TP), initial_concentration={CL: 0.15})
    for _ in range(200):
        o = _step(m, **SUMMER, **{B.INTAKE.format(CL): 0.03})
        assert o[STORED_MASS.format(CL)] / o[VOL] == pytest.approx(5.0 * 0.03, rel=1e-9)
        assert o[R_] == pytest.approx(o[C_] / 4.0, rel=1e-9)


def test_no_plant_heat_is_no_forced_evaporation():
    m = _pond(heat_mw=0)
    for i in range(24 * 10):
        o = _step(m, **_weather(i))
        assert o["water_user_water__forced_evaporation_volume_flux"] == pytest.approx(0.0, abs=1e-12)


def test_the_plants_heat_warms_the_pond_and_evaporates_water():
    hot, none = _pond(time_step=86400), _pond(heat_mw=0, time_step=86400)
    for _ in range(200):
        a, b = _step(hot, **SUMMER), _step(none, **SUMMER)
    assert a[TP] > b[TP] + 2
    forced = a["water_user_water__forced_evaporation_volume_flux"]
    assert forced == pytest.approx(a[C_] - b[C_], rel=1e-9)
    share = forced * physics.RHO * physics.LV / 500e6                # the share of the added heat leaving as evaporation
    assert 0.4 < share < 0.9


def test_the_step_length_does_not_move_the_equilibrium():
    """The heat balance is solved implicitly: hourly and daily steps on the same steady weather settle at the same temperature."""
    hourly, daily = _pond(time_step=3600), _pond(time_step=86400)
    for _ in range(24 * 400):
        a = _step(hourly, **SUMMER)
    for _ in range(400):
        b = _step(daily, **SUMMER)
    assert a[TP] == pytest.approx(b[TP], abs=1e-6)
    assert a[C_] == pytest.approx(b[C_], rel=1e-6)


def test_under_a_limit_blowdown_goes_first_then_storage():
    free, capped = _pond(time_step=86400), _pond(time_step=86400)
    for _ in range(100):
        a = _step(free, **SUMMER)
        _step(capped, **SUMMER)
    blowdown_cut = a[W_] - a["water_user_water__stream_return_volume_flux"] * 0.999       # just under the blowdown: storage holds
    o = _step(capped, **SUMMER, **{B.LIMIT: blowdown_cut})
    assert o[W_] == pytest.approx(blowdown_cut, rel=1e-12)
    assert o[DV] == pytest.approx(0.0, abs=1e-9 * a[W_])
    assert o["water_user_water__stream_return_volume_flux"] < a["water_user_water__stream_return_volume_flux"]
    volumes, temps = [], []
    for _ in range(60):                                          # a hard limit: the pond draws down and warms
        o = _step(capped, **SUMMER, **{B.LIMIT: 0.05})
        volumes.append(o[VOL])
        temps.append(o[TP])
    assert all(b < a for a, b in zip(volumes, volumes[1:]))
    assert temps[-1] > a[TP]
    assert o["water_user_water__stream_return_volume_flux"] == 0.0


def test_dry_mode_is_a_limit_of_zero():
    a, b = _pond(), _pond()
    for i in range(48):
        x = _step(a, **_weather(i), **{B.DRY_MODE: 1.0})
        y = _step(b, **_weather(i), **{B.LIMIT: 0.0})
        assert x == y and x[W_] == 0.0


def test_below_its_lowest_volume_the_plant_heat_is_not_taken():
    m = _pond(initial_volume_share=0.31, parameters={"min_volume_share": 0.3}, time_step=86400)
    lost = []
    for _ in range(30):
        o = _step(m, **SUMMER, **{B.DRY_MODE: 1.0})
        lost.append(o["water_user__unremoved_heat_power"])
    assert lost[0] == 0.0 and lost[-1] == 500.0
    assert o["water_user__setpoint_lost_time"] > 0
    assert o[VOL] < 0.3 * POND["area_m2"] * POND["depth_m"]


def test_a_hot_pond_counts_lost_hours_but_takes_the_heat():
    m = _pond(heat_mw=2000, parameters={"max_supply_c": 30.0}, time_step=86400)
    for _ in range(60):
        o = _step(m, **SUMMER)
    assert o[TP] > 30 and o["water_user__unremoved_heat_power"] == 0.0
    assert o["water_user__setpoint_lost_time"] > 0


def test_ice_is_not_modelled_the_pond_holds_at_zero():
    m = _pond(heat_mw=0, initial_temperature=1.0)
    for _ in range(48):
        o = _step(m, **{TEMP: -15.0, RH: 70.0, WIND: 6.0, SW: 0.0, LW: 200.0})
    f = m._last
    assert o[TP] == 0.0 and f["freeze_heat"] > 0


def test_rain_on_a_full_pond_spills():
    m = _pond(initial_volume_share=1.0)
    o = _step(m, **{**SUMMER, RAIN: 0.02})                          # 72 mm in the hour
    assert o[VOL] == pytest.approx(POND["area_m2"] * POND["depth_m"], rel=1e-12)
    assert o["water_user_water__stream_return_volume_flux"] > o[G_] * 0.9


def test_heat_set_each_step_wins_and_a_data_center_shortcut():
    m = _pond()
    a = _step(m, **SUMMER, **{HEAT: 100.0})
    assert m._last["heat_in"] == 100e6
    _step(m, **SUMMER)                                              # an input holds until it is set again
    assert m._last["heat_in"] == 100e6
    b = _step(m, **SUMMER, **{HEAT: math.nan})                      # NaN: back to the configured heat
    assert m._last["heat_in"] == 500e6
    assert a != b
    dc = CoolingPondBmi()
    dc.initialize({"area_m2": 1e6, "depth_m": 3, "it_capacity_mw": 100, "parameters": {"utilization": 0.8, "heat_factor": 1.1}})
    _step(dc, **SUMMER)
    assert dc._last["heat_in"] == pytest.approx(100e6 * 0.8 * 1.1, rel=1e-12)


def test_makeup_temperature_defaults_to_the_air():
    a, b = _pond(), _pond()
    x = _step(a, **SUMMER)
    y = _step(b, **SUMMER, **{MAKEUP_T: SUMMER[TEMP]})
    assert x == y


@pytest.mark.parametrize("cfg, match", [({"area_m2": 1e6}, "depth_m"), ({"area_m2": 1e6, "depth_m": 3, "heat_mw": 1, "it_capacity_mw": 1}, "not both"),
                                        ({"area_m2": 1e6, "depth_m": 3, "parameters": {"coc": 1.0}}, "above 1"),
                                        ({"area_m2": 1e6, "depth_m": 3, "parameters": {"bogus": 1}}, "unknown")])
def test_bad_configurations_are_refused(cfg, match):
    with pytest.raises(ValueError, match=match):
        CoolingPondBmi().initialize(cfg)
