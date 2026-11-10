"""Battery cell plants (design 0009, model 1.12): energy and water close hour by hour, the designs order as they should, output scales the
lines and not the fixed share, and the Monte Carlo reads what the hours give."""
import json
import os

import numpy as np
import pytest

from waterledger_models import heat_rejection as hr
from waterledger_models import once_through as ot
from waterledger_models.battery import physics as bp
from waterledger_models.battery import plant

HERE = os.path.dirname(__file__)
_W = json.load(open(os.path.join(HERE, "data", "west_michigan_2023_2024.json")))
TDB = np.array(_W["temperature_2m"], dtype=float)
RH = np.array(_W["relative_humidity_2m"], dtype=float)
TWB = hr.wet_bulb(TDB, RH)
TIMES = [str(t)[:13].replace(" ", "T") + ":00" for t in np.datetime64(_W["start"][:13]) + np.arange(len(TDB)).astype("timedelta64[h]")]
LAKE_MICHIGAN = json.load(open(os.path.join(HERE, "data", "water_ledger_lakes.json")))["Lake Michigan"]["temps"]
WATER_T = plant.lake_hours(TIMES, LAKE_MICHIGAN)


def central(**kw):
    return bp.for_location({**bp.central_parameters(), "utilization": 1.0, **kw}, TDB, RH)


@pytest.mark.parametrize("design", bp.DESIGNS)
@pytest.mark.parametrize("seed", [1, 2, 3])
def test_energy_and_water_close(design, seed):
    """Electricity + fuel + outdoor air's heat = heat rejected + exhaust + the heat rejection fans' heat; withdrawn = consumed + returned."""
    v = bp.sample_parameters(5, seed)
    for i in range(5):
        p = bp.for_location({k: float(a[i]) for k, a in v.items()}, TDB, RH)
        h = bp.hourly(TDB, TWB, RH, design, p, WATER_T)
        assert np.allclose(h["electricity"] + h["fuel"] + h["outdoor_air"], h["heat"] + h["exhaust"] + h["fans"], rtol=1e-12, atol=1e-9)
        assert np.allclose(h["withdrawn"], h["consumed"] + h["returned"], rtol=1e-12, atol=1e-12)
        assert np.allclose(h["withdrawn"], h["evap"] + h["drift"] + h["blow"] + h["once_through"] + h["process_withdrawn"] + h["staff"], rtol=1e-12)
        assert np.allclose(h["returned"], h["to_sewer"] + h["to_source"], rtol=1e-12, atol=1e-12)
        assert (h["returned"] >= 0).all() and (h["outdoor_air"] >= 0).all()


@pytest.mark.parametrize("design", bp.DESIGNS)
def test_returns_by_destination(design):
    """The sewer takes blowdown, process returns and staff water; only the lake design returns water to its source, the once-through water less
    the evaporation its heat drives."""
    p = central()
    h = bp.hourly(TDB, TWB, RH, design, p, WATER_T)
    process_and_staff = h["process_withdrawn"] - h["process_consumed"] + h["staff"] * (1 - p["staff_used"])
    assert np.allclose(h["to_sewer"], h["blow"] + process_and_staff, rtol=1e-12)
    if design == "lake":
        assert np.allclose(h["to_source"], h["once_through"] - h["lake_evap"], rtol=1e-12) and (h["to_source"] > 0).all()
    else:
        assert not h["to_source"].any()


def test_designs_order():
    w = {d: bp.hourly(TDB, TWB, RH, d, central(), WATER_T)["withdrawn"].mean() for d in bp.DESIGNS}
    c = {d: bp.hourly(TDB, TWB, RH, d, central(), WATER_T)["consumed"].mean() for d in bp.DESIGNS}
    assert w["dry"] < w["hybrid"] < w["towers"] < w["lake"] / 20
    assert c["dry"] < c["lake"] < c["towers"]
    dry = bp.hourly(TDB, TWB, RH, "dry", central())
    assert not dry["evap"].any() and not dry["blow"].any() and not dry["once_through"].any()


def test_lake_water_carries_the_heat():
    """Once through: the water drawn is the heat over its rise, the forced evaporation the share of that heat USGS's balance gives, and no towers run."""
    p = central()
    h = bp.hourly(TDB, TWB, RH, "lake", p, WATER_T)
    assert not (h["evap"].any() or h["blow"].any() or h["fans"].any())
    m3s = h["once_through"] / (3600.0 * ot.GAL_M3)
    assert np.allclose(m3s * ot.RHO * ot.CP * p["rise_c"], h["heat"] * 1000.0, rtol=1e-12)
    share = ot.evaporation_ratio(WATER_T, p["wind_mph"]) * p["evap_error"]
    assert np.allclose(h["lake_evap"] / (3600.0 * ot.GAL_M3) * ot.LV * ot.RHO, share * h["heat"] * 1000.0, rtol=1e-12)
    # chillers run only when the lake water is too warm for the chilled loop
    cold = WATER_T + p["hx_approach"] <= p["chilled_supply"]
    towers = bp.hourly(TDB, TWB, RH, "towers", p)
    assert (h["electricity"][cold] < towers["electricity"][cold]).all()
    with pytest.raises(ValueError):
        bp.hourly(TDB, TWB, RH, "lake", p)


def test_output_scales_the_lines_not_the_fixed_share():
    full, half = bp.hourly(TDB, TWB, RH, "towers", central()), bp.hourly(TDB, TWB, RH, "towers", central(utilization=0.5))
    phi = bp.central_parameters()["fixed_share"]
    assert half["energy"].mean() / full["energy"].mean() == pytest.approx(phi + (1 - phi) * 0.5)
    assert half["staff"].mean() == full["staff"].mean()


def test_outdoor_air_follows_enthalpy():
    p = central()
    h = bp.hourly(TDB, TWB, RH, "towers", p)
    cold = bp.enthalpy(TDB, RH) <= p["oa_supply_enthalpy"]
    assert not h["outdoor_air"][cold].any() and h["outdoor_air"][~cold].min() > 0
    design = p["oa_share"] / (1 - p["oa_share"]) * p["to_water"] * p["energy"] * bp.CELLS_PER_HOUR
    assert np.quantile(h["outdoor_air"], 0.996) == pytest.approx(design, rel=1e-6)


def test_central_plant_energy_is_in_the_published_range():
    """Plant energy with the cooling plant's own work added back lands in 25-45 kWh per kWh of cells (Kuki et al. 2025; UKBIC 2022)."""
    for d in bp.DESIGNS:
        h = bp.hourly(TDB, TWB, RH, d, central(), WATER_T)
        assert 25 < (h["electricity"] + h["fuel"]).mean() / bp.CELLS_PER_HOUR < 45


def test_monte_carlo_reads_the_hours():
    r = plant.run_location(TIMES, TDB, RH, n=20, gwh=10.0)
    h = bp.hourly(TDB, TWB, RH, "towers", central())
    c = r["towers"]
    assert c["withdrawn_avg"]["central"] == pytest.approx(h["withdrawn"].mean() * 24 * 10 / 1e6, rel=1e-9)
    assert c["power_mw_avg"]["central"] == pytest.approx(h["electricity"].mean() * 10 / 1000, rel=1e-12)
    assert c["utilization"]["p10"] == c["utilization"]["p90"] == 1.0
    assert c["withdrawn_peak_1in10"]["p50"] > c["withdrawn_avg"]["p50"]
    assert c["returned_avg"]["central"] == pytest.approx(c["to_sewer_avg"]["central"] + c["to_source_avg"]["central"], rel=1e-12)
    # the highest hour is above the highest day, which is above the average, and the hour is read from the hours
    assert c["power_mw_peak_1in10"]["p50"] > c["power_mw_peak_day_1in10"]["p50"] > c["power_mw_avg"]["p50"]
    years = np.array([t[:4] for t in TIMES])
    assert c["power_mw_peak_1in10"]["central"] == pytest.approx(
        np.quantile([h["electricity"][years == y].max() for y in np.unique(years)], 0.9) * 10 / 1000, rel=1e-12)
    s = plant.run_location(TIMES, TDB, RH, n=20, gwh=10.0, utilization="sampled", designs=("towers",))["towers"]
    assert s["utilization"]["p10"] < 1.0 and s["withdrawn_avg"]["p50"] < c["withdrawn_avg"]["p50"]
    with pytest.raises(ValueError):
        plant.run_location(TIMES, TDB, RH, n=2, utilization="half")
    assert set(r) == {"dry", "hybrid", "towers"}
    lake = plant.run_location(TIMES, TDB, RH, n=4, gwh=10.0, water_temps=LAKE_MICHIGAN)
    assert set(lake) == set(bp.DESIGNS) and lake["lake"]["withdrawn_avg"]["p50"] > 20 * c["withdrawn_avg"]["p50"]


def test_lake_hours_follow_the_calendar():
    t = plant.lake_hours(["2023-01-01T00:00", "2023-12-31T23:00", "2024-12-31T05:00"], np.arange(366.0))
    assert t.tolist() == [0.0, 364.0, 365.0]


def test_settings_fix_a_plants_own_operating_values():
    """A plant's documents can set its cycles of concentration: every run takes them, fewer cycles bleed off more water and evaporate the same."""
    runs = plant.draws(10, settings={"coc": 3.0})
    assert all(p["coc"] == 3.0 and p["utilization"] == 1.0 for p in runs)
    three = plant.run_location(TIMES, TDB, RH, n=10, gwh=10.0, designs=("towers",), settings={"coc": 3.0})["towers"]
    six = plant.run_location(TIMES, TDB, RH, n=10, gwh=10.0, designs=("towers",), settings={"coc": 6.0})["towers"]
    assert three["withdrawn_avg"]["p50"] > six["withdrawn_avg"]["p50"]
    assert three["consumed_avg"]["central"] == pytest.approx(six["consumed_avg"]["central"], rel=1e-12)
    with pytest.raises(ValueError):
        plant.draws(2, settings={"cycles": 3.0})


def test_lfp_scales_the_plant_energy():
    """An LFP plant's energy per kWh is the NMC plant's times lfp_factor, and its heat and cooling water follow; an NMC plant's runs are the
    draws they were before chemistry, with no lfp_factor."""
    nmc, lfp = central(), central(lfp_factor=1.4)
    a, b = bp.hourly(TDB, TWB, RH, "towers", nmc), bp.hourly(TDB, TWB, RH, "towers", lfp)
    assert np.allclose(b["energy"], 1.4 * a["energy"], rtol=1e-12)
    assert b["evap"].mean() / a["evap"].mean() == pytest.approx(1.4, rel=0.02)
    assert np.allclose(b["process_withdrawn"], a["process_withdrawn"]) and np.allclose(b["staff"], a["staff"])
    plain = plant.draws(6)
    assert all("lfp_factor" not in p for p in plain)
    with_lfp = plant.draws(6, chemistry="lfp")
    assert all(1.2 <= p["lfp_factor"] <= 1.7 for p in with_lfp) and with_lfp[-1]["lfp_factor"] == pytest.approx(1.45)
    assert [{k: v for k, v in p.items() if k != "lfp_factor"} for p in with_lfp] == plain
    r = {c: plant.run_location(TIMES, TDB, RH, n=10, gwh=10.0, designs=("towers",), chemistry=c)["towers"] for c in bp.CHEMISTRIES}
    assert r["lfp"]["withdrawn_avg"]["p50"] > 1.15 * r["nmc"]["withdrawn_avg"]["p50"]
    with pytest.raises(ValueError):
        plant.draws(2, chemistry="sodium")
    with pytest.raises(ValueError):
        plant.draws(2, settings={"lfp_factor": 1.5})
