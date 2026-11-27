"""get_state and set_state on every BMI component (design 0024): a run saved partway, loaded into a fresh component initialized the
same way and run on, matches the run that never stopped, to the bit; a state is refused by a component set up differently."""
import json

import numpy as np
import pytest

from waterledger_models import grid, state
from waterledger_models.battery.bmi import BatteryCellBmi
from waterledger_models.datacenter import bmi as B
from waterledger_models.datacenter.bmi import CoolingWaterBmi, LakeCoolingBmi
from waterledger_models.gas.bmi import GasPlantBmi
from waterledger_models.grid.bmi import GridWaterBmi
from waterledger_models.ponds import bmi as P
from test_grid_component import synthetic
from test_physics_properties import synthetic_weather

TEMP = "atmosphere_bottom_air__temperature"
RH = "atmosphere_bottom_air_water_vapor__relative_saturation"


def _open_meteo(tmp_path, days=4):
    time, t, rh = synthetic_weather(days)
    path = tmp_path / "weather.json"
    path.write_text(json.dumps({"hourly": {"time": [str(x) for x in time.astype("datetime64[m]")],
                                           "temperature_2m": t.tolist(), "relative_humidity_2m": rh.tolist()}}), encoding="utf-8")
    return str(path)


def _grid_table():
    hour, c, w, g, t = synthetic()
    return grid.fit("TEST", hour, c, w, g, t)


def _inputs(cls, step):
    """Inputs a framework sets each step, varied so every step differs (none for a component reading its own forcing)."""
    hot = 22 + 14 * np.sin(step / 3.0)
    if cls is LakeCoolingBmi:
        return {"lake_water_surface__temperature": 4 + 0.5 * step, "atmosphere_bottom_air_flow__speed": 3 + (step % 5)}
    if cls is GridWaterBmi:
        return {"water_user__electric_power": 100 + 10 * (step % 7), TEMP: hot}
    if cls is CoolingWaterBmi:          # a limit that binds on hot hours, so heat not removed and the lost hours (a running sum) move
        return {TEMP: hot, RH: 45 + 3 * (step % 9), B.LIMIT: 0.05 if step % 4 == 0 else np.inf, B.INTAKE.format("chloride"): 0.03}
    if cls is P.CoolingPondBmi:         # a limit some days, so the pond draws down and refills: its volume, heat and mass carry
        return {TEMP: hot, RH: 45 + 3 * (step % 9), P.WIND: 2 + step % 4, P.SW: 200 + 20 * (step % 5), P.LW: 350.0,
                P.RAIN: 0.01 if step % 6 == 0 else 0.0, B.LIMIT: 0.05 if 5 <= step < 20 else np.inf, B.INTAKE.format("chloride"): 0.03}
    if cls is P.TailingsPondBmi:        # a limit some days and the mill slowed on others: the pool, tailings, heat and mass carry
        return {TEMP: hot, RH: 45 + 3 * (step % 9), P.WIND: 2 + step % 4, P.SW: 200 + 20 * (step % 5), P.LW: 350.0,
                P.RAIN: 0.01 if step % 6 == 0 else 0.0, B.LIMIT: 0.02 if 5 <= step < 20 else np.inf,
                P.SOLIDS: 20.0 if step % 7 == 3 else np.nan, B.INTAKE.format("dissolved_solids"): 0.4}
    if cls is GasPlantBmi:
        return {TEMP: hot, RH: 45 + 3 * (step % 9), "power_plant__electric_power_demand": 300 + 250 * np.sin(step / 5.0)}
    return {TEMP: hot, RH: 45 + 3 * (step % 9)}


CASES = {
    "cooling towers": (CoolingWaterBmi, lambda tmp: {"design": "towers", "it_capacity_mw": 300, "parameters": {"design_db": 31.0}}),
    "cooling hybrid, forcing": (CoolingWaterBmi, lambda tmp: {"design": "hybrid", "it_capacity_mw": 50, "forcing": _open_meteo(tmp)}),
    "lake": (LakeCoolingBmi, lambda tmp: {"it_capacity_mw": 100}),
    "battery": (BatteryCellBmi, lambda tmp: {"design": "towers", "capacity_gwh": 10, "parameters": {"design_h": 70.0}}),
    "gas": (GasPlantBmi, lambda tmp: {"technology": "cc", "design": "towers", "units": 2, "unit_mw": 300}),
    "cooling pond": (P.CoolingPondBmi, lambda tmp: {"area_m2": 2e5, "depth_m": 2.0, "heat_mw": 40, "time_step": 86400}),
    "tailings pond": (P.TailingsPondBmi, lambda tmp: {"capacity_m3": 2e6, "capacity_area_m2": 4e5, "tailings_t_per_day": 2000,
                                                      "initial_pool_m3": 1.5e5, "min_pool_m3": 1.2e5, "time_step": 86400,
                                                      "initial_concentration": {"dissolved_solids": 1.0}}),
    "grid": (GridWaterBmi, lambda tmp: {"table": _grid_table(), "start": "2021-07-01T00"}),
}


def _run(m, cls, first, last, forced):
    rows = []
    for step in range(first, last):
        if not forced:
            for k, v in _inputs(cls, step).items():
                m.set_value(k, np.array([v]))
        m.update()
        rows.append({k: m.get_value(k, np.empty(1))[0] for k in m.get_output_var_names()})
    return rows


def _same(a, b):
    """Equal to the bit, NaN included."""
    return np.array(a, dtype=float).tobytes() == np.array(b, dtype=float).tobytes()


@pytest.mark.parametrize("case", CASES)
def test_a_saved_run_carries_on_to_the_bit(case, tmp_path):
    cls, cfg = CASES[case]
    config = cfg(tmp_path)
    forced = "forcing" in config
    whole = cls()
    whole.initialize(config)
    rows = _run(whole, cls, 0, 30, forced)

    first = cls()
    first.initialize(config)
    _run(first, cls, 0, 12, forced)
    if not forced:                                  # inputs set for the next step, before the save, carry with the state
        for k, v in _inputs(cls, 12).items():
            first.set_value(k, np.array([v]))
    saved = first.get_state()
    assert isinstance(saved, str)
    json.loads(saved)                               # standard JSON

    second = cls()
    second.initialize(config)
    ptr = second.get_value_ptr(second.get_output_var_names()[0])
    second.set_state(saved)
    assert second.get_current_time() == first.get_current_time() == 12 * second.get_time_step()
    if not forced:
        second.update()                             # step 12 on the inputs set before the save, no new set_value
        rest = [{k: second.get_value(k, np.empty(1))[0] for k in second.get_output_var_names()}] + _run(second, cls, 13, 30, forced)
    else:
        rest = _run(second, cls, 12, 30, forced)
    assert ptr is second.get_value_ptr(second.get_output_var_names()[0])       # pointers taken before the load stay live
    for a, b in zip(rows[12:], rest):
        assert _same(list(a.values()), list(b.values()))
    assert second.get_state() == whole.get_state()   # and the states agree at the end


def test_the_running_sum_carries():
    """CoolingWaterBmi's lost hours are summed since initialize: the one output that carries from step to step today."""
    cfg = {"design": "towers", "it_capacity_mw": 300}
    a = CoolingWaterBmi()
    a.initialize(cfg)
    for _ in range(3):
        a.set_value(TEMP, np.array([35.0]))
        a.set_value(RH, np.array([60.0]))
        a.set_value(B.LIMIT, np.array([0.01]))
        a.update()
    lost = a.get_value("data_center__setpoint_lost_time", np.empty(1))[0]
    assert lost == 3.0
    b = CoolingWaterBmi()
    b.initialize(cfg)
    b.set_state(a.get_state())
    assert b.get_value("data_center__setpoint_lost_time", np.empty(1))[0] == lost
    assert b.get_value(B.LIMIT, np.empty(1))[0] == 0.01


def test_a_state_is_refused_by_a_component_set_up_differently(tmp_path):
    a = CoolingWaterBmi()
    a.initialize({"design": "towers", "it_capacity_mw": 100})
    a.update()
    saved = a.get_state()
    for other in ({"design": "towers", "it_capacity_mw": 101}, {"design": "assist", "it_capacity_mw": 100, "parameters": {"design_db": 31.0}},
                  {"design": "towers", "it_capacity_mw": 100, "parameters": {"coc": 6}}, {"design": "towers", "it_capacity_mw": 100, "time_step": 1800}):
        b = CoolingWaterBmi()
        b.initialize(other)
        with pytest.raises(ValueError, match="initialized differently"):
            b.set_state(saved)
    lake = LakeCoolingBmi()
    lake.initialize({})
    with pytest.raises(ValueError, match="a state of"):
        lake.set_state(saved)
    # the same forcing file name with other weather in it
    f1 = _open_meteo(tmp_path, days=4)
    h1 = CoolingWaterBmi()
    h1.initialize({"design": "hybrid", "forcing": f1})
    h1.update()
    saved = h1.get_state()
    _open_meteo(tmp_path, days=5)
    h2 = CoolingWaterBmi()
    h2.initialize({"design": "hybrid", "forcing": f1})
    with pytest.raises(ValueError, match="initialized differently"):
        h2.set_state(saved)


def test_other_versions_and_strings_are_refused():
    a = CoolingWaterBmi()
    a.initialize({})
    s = json.loads(a.get_state())
    with pytest.raises(ValueError, match="version"):
        a.set_state(json.dumps({**s, "version": state.VERSION + 1}))
    with pytest.raises(ValueError, match="not a waterledger-models BMI state"):
        a.set_state(json.dumps({"time": 0}))


def test_a_state_holds_infinity_and_nan_exactly():
    a = CoolingWaterBmi()
    a.initialize({})
    a.set_value(TEMP, np.array([np.nan]))
    s = a.get_state()
    assert "Infinity" not in s and "NaN" not in s         # standard JSON: floats as hex
    b = CoolingWaterBmi()
    b.initialize({})
    b.set_state(s)
    assert np.isinf(b.get_value(B.LIMIT, np.empty(1))[0]) and np.isnan(b.get_value(TEMP, np.empty(1))[0])


@pytest.mark.parametrize("value", [0.1, -0.0, np.inf, 3, True, np.True_, None, "x", [1.5, 2], (1, 2.5), {"a": {"b": np.float64(1e-300)}},
                                   np.arange(6, dtype=float).reshape(2, 3) / 7, np.array([1, 2], dtype=np.int32)])
def test_pack_round_trips(value):
    back = state.unpack(json.loads(json.dumps(state.pack(value))))
    if isinstance(value, np.ndarray):
        assert back.dtype == value.dtype and back.shape == value.shape and back.tobytes() == value.tobytes()
    else:
        assert repr(back) == repr(value if not isinstance(value, np.floating) else float(value)) or back == value
