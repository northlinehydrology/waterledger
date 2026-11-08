"""The cooling plant inside the building (model 1.10, design 0007): each plant's ranges and link, the glycol loop's properties, and the plant
carried from the cooling runs through a cell record to an estimate."""
import numpy as np
import pytest

from waterledger import scenario as sc
from waterledger.national import era5 as E
from waterledger_models.datacenter import bmi, cooling, physics as ph

T = np.arange(-25.0, 41.0, 1.0)
W = ph.wet_bulb(T, np.full_like(T, 55.0))


def test_shared_is_the_default_and_every_plant_has_a_label():
    assert ph.DEFAULT_PLANT == "shared" == sc.DEFAULT_PLANT
    assert set(ph.PLANT_LABELS) == set(ph.PLANTS) == set(ph.SHARED)
    assert ph.central_parameters() == ph.central_parameters("shared")


@pytest.mark.parametrize("plant", [k for k in ph.PLANTS if ph.SHARED[k]])
def test_where_the_racks_share_the_air_loop_their_water_is_the_air_loops(plant):
    v = ph.sample_parameters(50, 7, plant)
    assert np.allclose(v["liquid_water"], ph.air_loop_water(v))
    c = ph.central_parameters(plant)
    assert c["liquid_water"] == pytest.approx(ph.air_loop_water(c))
    assert ph.loop_limit(c) == pytest.approx(ph.air_loop_water(c) - c["dc_approach"] - c["hx_approach"])


def test_the_shared_loops_water_is_the_coil_relations_from_24_30_c_air():
    c = ph.central_parameters("shared")
    assert c["supply_air"] == 27.0
    assert c["liquid_water"] == pytest.approx(27.0 + c["air_rise"] - c["air_rise"] / c["coil_eff"])
    assert 22.0 < c["liquid_water"] < 24.0           # OCP 2024's shared loop runs 24 C supply; Uptime's 18-24 C at the coolant units


def test_the_warm_plant_keeps_its_own_loop_and_mostly_liquid_racks():
    v = ph.sample_parameters(200, 7, "warm")
    assert v["liquid_water"].min() >= 30.0 and v["liquid_water"].max() <= 42.0 and v["liquid_share"].min() >= 0.7
    assert not np.allclose(v["liquid_water"], ph.air_loop_water(v))


def test_the_chilled_plant_sets_its_water_and_runs_cold_air():
    c = ph.central_parameters("chilled")
    assert "chilled_water" not in ph.central_parameters("shared") and "chilled_water" not in ph.central_parameters("warm")
    assert ph.air_loop_water(c) == c["chilled_water"] == 10.0 and c["supply_air"] == 20.0 and c["liquid_water"] == 10.0
    v = ph.sample_parameters(200, 7, "chilled")
    assert v["chilled_water"].min() >= 7.0 and v["chilled_water"].max() <= 13.0 and v["liquid_share"].max() <= 0.2


def test_colder_loops_take_more_electricity_and_hybrid_more_water():
    """Over a year of temperatures, the chilled plant takes the most facility power and the warm plant the least, for every design; hybrid evaporates more on
    colder loops, since its switch point follows the loop. Towers' water hardly moves."""
    p = {k: {**ph.central_parameters(k), "design_db": 30.0} for k in ph.PLANTS}
    for design in ph.DESIGNS:
        power = {k: ph.hourly_heat_power(T, W, design, p[k])[0].mean() for k in ph.PLANTS}
        assert power["warm"] < power["shared"] < power["chilled"], design
    water = {k: ph.hourly_rates(T, W, "hybrid", p[k])[0].mean() for k in ph.PLANTS}
    assert water["warm"] < water["shared"] <= water["chilled"]
    towers = [ph.hourly_rates(T, W, "towers", p[k])[0].mean() for k in ph.PLANTS]
    assert max(towers) / min(towers) < 1.1


def test_the_glycols_properties_are_dows_at_30_and_40_percent():
    assert ph.glycol_properties({"glycol_share": 0.30}) == pytest.approx((3.870, 1025.2))
    assert ph.glycol_properties({"glycol_share": 0.40}) == pytest.approx((3.701, 1036.9))
    cp, rho = ph.glycol_properties({"glycol_share": 0.35})
    assert 3.70 < cp < 3.87 < ph.CP_WATER and rho > ph.RHO_WATER


def test_glycol_takes_more_pump_power_than_water_would():
    """Less heat per kilogram means more flow for the same heat: the dry coolers' pump takes more with glycol than with water's properties."""
    p = {**ph.central_parameters(), "oa_cfm_per_mw": 0.0}
    t, wb = np.array([-10.0]), np.array([-11.0])
    pump = lambda q: ph.hourly_heat_power(t, wb, "dry", q)[0] - ph.hourly_heat_power(t, wb, "dry", {**q, "pump_tower_kpa": 0.0})[0]
    as_water = dict(ph.GLYCOL)
    try:
        ph.GLYCOL.update({0.30: (ph.CP_WATER, ph.RHO_WATER), 0.40: (ph.CP_WATER, ph.RHO_WATER)})
        water = pump(p)
    finally:
        ph.GLYCOL.clear()
        ph.GLYCOL.update(as_water)
    assert pump(p)[0] > water[0] * 1.05


def test_a_plant_that_doesnt_exist_stops():
    with pytest.raises(ValueError, match="plant must be one of"):
        ph.sample_parameters(10, 7, "immersion")
    with pytest.raises(ValueError, match="plant must be one of"):
        ph.central_parameters("immersion")


def test_run_plants_runs_each_plant_default_first():
    times = [f"2025-07-{d:02d}T{h:02d}:00" for d in range(1, 3) for h in range(24)]
    temps = [20.0 + 8.0 * np.sin(np.pi * (h - 9) / 12) for _ in range(2) for h in range(24)]
    rhs = [60.0] * len(times)
    got = cooling.run_plants(times, temps, rhs, n=4)
    assert list(got) == ["shared", "warm", "chilled"]
    assert got["shared"] == cooling.run_location(times, temps, rhs, n=4)
    assert got["warm"]["dry"]["power_mw_avg"]["p50"] < got["shared"]["dry"]["power_mw_avg"]["p50"] < got["chilled"]["dry"]["power_mw_avg"]["p50"]


def test_a_cell_record_keeps_the_default_under_per_100mw_and_the_others_beside_it():
    res = {"shared": {"dry": 1}, "warm": {"dry": 2}, "chilled": {"dry": 3}}
    assert E.by_plant(res) == {"plant": "shared", "per_100mw": {"dry": 1}, "per_100mw_plants": {"warm": {"dry": 2}, "chilled": {"dry": 3}}}
    assert E.by_plant({"dry": 1, "towers": 4}) == {"per_100mw": {"dry": 1, "towers": 4}}         # one plant's run, as before 1.10


def test_an_estimate_reads_the_plant_it_asks_for():
    rec = {"cell": "x", **E.by_plant({"shared": {"dry": 1}, "warm": {"dry": 2}, "chilled": {"dry": 3}})}
    assert sc.for_plant(rec)["per_100mw"] == {"dry": 1}
    assert sc.for_plant(rec, "warm")["per_100mw"] == {"dry": 2} and sc.for_plant(rec, "warm")["plant"] == "warm"
    assert sc.for_plant(rec, "chilled")["per_100mw"] == {"dry": 3}
    with pytest.raises(ValueError, match="results from before model 1.10 have one"):
        sc.for_plant({"per_100mw": {"dry": 1}}, "warm")
    assert sc.for_plant({"per_100mw": {"dry": 1}})["per_100mw"] == {"dry": 1}


def test_the_bmi_takes_a_plant_and_guards_its_linked_values():
    m = bmi.CoolingWaterBmi()
    m.initialize({"design": "towers", "plant": "warm", "parameters": {"liquid_water": 40.0}})
    assert m._params["liquid_water"] == 40.0
    m.initialize({"design": "towers"})
    assert m._params["liquid_water"] == pytest.approx(ph.air_loop_water(m._params))
    m.initialize({"design": "towers", "parameters": {"supply_air": 25.0}})
    assert m._params["liquid_water"] == pytest.approx(ph.air_loop_water(m._params)) and m._params["supply_air"] == 25.0
    with pytest.raises(ValueError, match="air loop's water"):
        m.initialize({"design": "towers", "parameters": {"liquid_water": 40.0}})
    with pytest.raises(ValueError, match="chilled plant's"):
        m.initialize({"design": "towers", "plant": "warm", "parameters": {"chilled_water": 9.0}})
    with pytest.raises(ValueError, match="plant must be one of"):
        m.initialize({"design": "towers", "plant": "immersion"})
