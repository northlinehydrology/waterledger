"""Battery cell plants (design 0009, model 1.12): energy and water close hour by hour, the designs order as they should, output scales the
lines and not the fixed share, and the Monte Carlo reads what the hours give."""
import json
import os

import numpy as np
import pytest

from waterledger_models import heat_rejection as hr
from waterledger_models.battery import physics as bp
from waterledger_models.battery import plant

HERE = os.path.dirname(__file__)
_W = json.load(open(os.path.join(HERE, "data", "west_michigan_2023_2024.json")))
TDB = np.array(_W["temperature_2m"], dtype=float)
RH = np.array(_W["relative_humidity_2m"], dtype=float)
TWB = hr.wet_bulb(TDB, RH)
TIMES = [str(t)[:13].replace(" ", "T") + ":00" for t in np.datetime64(_W["start"][:13]) + np.arange(len(TDB)).astype("timedelta64[h]")]


def central(**kw):
    return bp.for_location({**bp.central_parameters(), "utilization": 1.0, **kw}, TDB, RH)


@pytest.mark.parametrize("design", bp.DESIGNS)
@pytest.mark.parametrize("seed", [1, 2, 3])
def test_energy_and_water_close(design, seed):
    """Electricity + fuel + outdoor air's heat = heat rejected + exhaust + the heat rejection fans' heat; withdrawn = consumed + returned."""
    v = bp.sample_parameters(5, seed)
    for i in range(5):
        p = bp.for_location({k: float(a[i]) for k, a in v.items()}, TDB, RH)
        h = bp.hourly(TDB, TWB, RH, design, p)
        assert np.allclose(h["electricity"] + h["fuel"] + h["outdoor_air"], h["heat"] + h["exhaust"] + h["fans"], rtol=1e-12, atol=1e-9)
        assert np.allclose(h["withdrawn"], h["consumed"] + h["returned"], rtol=1e-12, atol=1e-12)
        assert np.allclose(h["withdrawn"], h["evap"] + h["drift"] + h["blow"] + h["process_withdrawn"] + h["staff"], rtol=1e-12)
        assert (h["returned"] >= 0).all() and (h["outdoor_air"] >= 0).all()


def test_designs_order():
    w = {d: bp.hourly(TDB, TWB, RH, d, central())["withdrawn"].mean() for d in bp.DESIGNS}
    assert w["dry"] < w["hybrid"] < w["towers"]
    dry = bp.hourly(TDB, TWB, RH, "dry", central())
    assert not dry["evap"].any() and not dry["blow"].any()


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
        h = bp.hourly(TDB, TWB, RH, d, central())
        assert 25 < (h["electricity"] + h["fuel"]).mean() / bp.CELLS_PER_HOUR < 45


def test_monte_carlo_reads_the_hours():
    r = plant.run_location(TIMES, TDB, RH, n=20, gwh=10.0)
    h = bp.hourly(TDB, TWB, RH, "towers", central())
    c = r["towers"]
    assert c["withdrawn_avg"]["central"] == pytest.approx(h["withdrawn"].mean() * 24 * 10 / 1e6, rel=1e-9)
    assert c["power_mw_avg"]["central"] == pytest.approx(h["electricity"].mean() * 10 / 1000, rel=1e-12)
    assert c["utilization"]["p10"] == c["utilization"]["p90"] == 1.0
    assert c["withdrawn_peak_1in10"]["p50"] > c["withdrawn_avg"]["p50"]
    s = plant.run_location(TIMES, TDB, RH, n=20, gwh=10.0, utilization="sampled", designs=("towers",))["towers"]
    assert s["utilization"]["p10"] < 1.0 and s["withdrawn_avg"]["p50"] < c["withdrawn_avg"]["p50"]
    with pytest.raises(ValueError):
        plant.run_location(TIMES, TDB, RH, n=2, utilization="half")


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
