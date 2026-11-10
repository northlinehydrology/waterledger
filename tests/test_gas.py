"""New gas plants (design 0014, step 2): balances every hour for every technology and design, the checks against public figures (0014's checks
1, 2 and 4), unserved hours reported, outages, and the Monte Carlo on the shared runner."""
import json
import os

import numpy as np
import pytest

from golden import weather
from waterledger_models import heat_rejection as hr
from waterledger_models.battery.plant import lake_hours
from waterledger_models.gas import physics as gp
from waterledger_models.gas import plant

HERE = os.path.dirname(__file__)
TIMES, T, RH = weather()
T, RH = np.asarray(T, float), np.asarray(RH, float)
TWB = hr.wet_bulb(T, RH)
LAKE = json.load(open(os.path.join(HERE, "data", "water_ledger_lakes.json")))["Lake Michigan"]["temps"]
WATER_T = lake_hours(TIMES, LAKE)
CASES = [(tech, d) for tech in gp.TECHNOLOGIES for d in gp.DESIGNS[tech]]


def _p(tech, design, nox="dln", **kw):
    return hr.for_location({**gp.central_parameters(tech, design, nox), **kw}, T)


@pytest.mark.parametrize("tech,design", CASES)
@pytest.mark.parametrize("cooling", [False, True])
def test_energy_and_water_close_every_hour(tech, design, cooling):
    """fuel = net + auxiliary + condenser + other, no term negative; withdrawn = consumed + returned, returned = to_sewer + to_source; served +
    unserved = demand. The demand swings from nothing to more than the plant can carry."""
    nox = "water" if tech in ("ct", "cc") else "dln"
    demand = 700.0 * (1 + np.sin(np.arange(len(T)) / 50.0))
    h = gp.hourly(demand, T, TWB, RH, tech, design, _p(tech, design, nox), 3, 250.0, inlet_cooling=cooling, water_t=WATER_T)
    np.testing.assert_allclose(h["fuel"], h["served"] + h["aux"] + h["condenser"] + h["other"], rtol=1e-12, atol=1e-9)
    for k in ("served", "unserved", "fuel", "aux", "condenser", "other", "evap", "blow", "once_through", "nox", "inlet"):
        assert (h[k] >= -1e-9).all(), k
    np.testing.assert_allclose(h["withdrawn"], h["consumed"] + h["returned"], rtol=1e-12, atol=1e-9)
    np.testing.assert_allclose(h["returned"], h["to_sewer"] + h["to_source"] + h["to_stream"], rtol=1e-12, atol=1e-9)
    np.testing.assert_allclose(h["served"] + h["unserved"], demand, rtol=1e-12)
    assert (h["unserved"] > 0).any() and (h["served"] <= h["capacity"] + 1e-9).all()


def test_netl_combined_cycle_at_iso():
    """0014 check 1: an F-class combined cycle on towers at 15 C and 60% relative humidity, 4 cycles, NETL B31A's own heat rate (1,355 MW of fuel
    for 727 net). NETL gives 186 gal/MWh consumed and 240 withdrawn (Rev. 4a, Exhibit ES-4). The model, at central values and nothing tuned, gives
    about 158 and 206: about 15% low. Most of it is the shared evaporative ratio, 0.77 at 15 C (Rutberg et al. 2011, the model's stated departure
    for every user: not all the heat evaporates in cool weather), the rest the condenser share (0.60 against NETL's 0.62). Held at 20%, and the
    finding is in the methods log, not tuned away."""
    n = 24 * 30
    tdb, rh = np.full(n, 15.0), np.full(n, 60.0)
    p = hr.for_location({**gp.central_parameters("cc", "towers"), "coc": 4.0, "heat_rate": 1355.0 / 727.0 * gp.KWH_BTU}, tdb)
    h = gp.hourly(727.0, tdb, hr.wet_bulb(tdb, rh), rh, "cc", "towers", p, 1, 727.0)
    consumed, withdrawn = h["consumed"].sum() / h["served"].sum(), h["withdrawn"].sum() / h["served"].sum()
    assert consumed == pytest.approx(186.0, rel=0.20) and withdrawn == pytest.approx(240.0, rel=0.20)
    assert consumed < 186.0 and withdrawn < 240.0          # low, not high: the direction the evaporative ratio takes it
    assert withdrawn / consumed == pytest.approx(4.0 / 3.0, rel=0.02)    # makeup over evaporation and drift at 4 cycles


def test_turbine_derate_at_100f():
    """0014 check 4: a simple-cycle turbine's output at 100 F within 3 points of the EPA CHP Catalog's 80% (p. 3-10); a combined cycle's derate
    with dry cooling above its wet one."""
    t = np.array([37.78])
    h = gp.hourly(1e6, t, hr.wet_bulb(t, np.array([30.0])), np.array([30.0]), "ct", "none", gp.central_parameters("ct", "none"), 1, 100.0)
    assert h["capacity"][0] == pytest.approx(80.0, abs=3.0)
    caps = {d: gp.hourly(1e6, t, hr.wet_bulb(t, np.array([30.0])), np.array([30.0]), "cc", d, hr.for_location(gp.central_parameters("cc", d), T),
                         1, 100.0)["capacity"][0] for d in ("towers", "dry")}
    assert caps["dry"] < caps["towers"] < 100.0


def test_a_year_of_weather_inside_the_published_ranges():
    """0014 check 2 on the stored West Michigan weather, 20 draws, the p10-p90 of water per MWh net against Macknick et al. 2012, Meldrum et al.
    2013 and USGS: towers 130-300 consumed and 150-290 withdrawn; dry about 0; once-through 7,200-21,000 withdrawn and 20-230 consumed; hybrid
    and assist between dry and towers; a simple-cycle turbine with water injection 24-56 consumed (the research note's derivation)."""
    def run(tech, design, **kw):
        r = plant.run_location(TIMES, T, RH, tech, design, 2, 300.0, n=20, **kw)[design]
        return r["consumed_gal_per_mwh"], r["withdrawn_gal_per_mwh"]
    c, w = run("cc", "towers")
    assert 130 <= c["p10"] and c["p90"] <= 300 and 150 <= w["p10"] and w["p90"] <= 290
    c, w = run("cc", "lake", water_temps=LAKE)
    assert 20 <= c["p10"] and c["p90"] <= 230 and 7200 <= w["p10"] and w["p90"] <= 21000
    assert run("cc", "dry")[1]["p90"] < 4.0
    towers = run("cc", "towers")[0]["p50"]
    assert all(0.0 < run("cc", d)[0]["p50"] < towers for d in ("hybrid", "assist"))
    c, _ = run("ct", "none", nox="water")
    assert 24 <= c["p10"] and c["p90"] <= 56


def test_inlet_cooling_trades_water_for_output():
    """Inlet evaporative cooling on a hot afternoon: more output, and about 7-16 gal per MWh in the hours it runs (the research note's S4)."""
    t, rh = np.full(24, 35.0), np.full(24, 30.0)
    twb = hr.wet_bulb(t, rh)
    p = hr.for_location(gp.central_parameters("ct", "none"), t)
    dry_inlet = gp.hourly(1e6, t, twb, rh, "ct", "none", p, 1, 100.0)
    wet_inlet = gp.hourly(1e6, t, twb, rh, "ct", "none", p, 1, 100.0, inlet_cooling=True)
    assert wet_inlet["served"][0] > dry_inlet["served"][0]
    assert 5.0 <= wet_inlet["inlet"][0] / wet_inlet["served"][0] <= 16.0


def test_unserved_and_outages():
    """Demand above the units available is unserved, never filled; with outages, units up each hour follow the availability."""
    up = gp.outages(4, 0.9, 100000, seed=3)
    assert up.max() <= 4 and up.mean() == pytest.approx(3.6, abs=0.02)
    h = gp.hourly(1000.0, T, TWB, RH, "engine", "dry", _p("engine", "dry"), 4, 200.0, available=up[:len(T)])
    assert (h["unserved"] >= 200.0 - 1e-9).all() and (h["unserved"] > 400.0).any()


def test_the_monte_carlo_on_the_shared_runner():
    r = plant.run_location(TIMES, T, RH, "cc", "towers", 2, 300.0, capacity_factor=0.8, n=6, outages=True)["towers"]
    for k in ("withdrawn_avg", "consumed_peak_1in10", "to_sewer_avg", "power_mw_avg", "net_mw_avg", "unserved_mw_avg", "heat_rate_avg"):
        assert k in r, k
    assert r["net_mw_avg"]["p50"] == pytest.approx(0.8 * 600.0, rel=0.06)       # nearly all of it served at N+0 with outages
    assert r["withdrawn_avg"]["central"] == pytest.approx(r["consumed_avg"]["central"] + r["returned_avg"]["central"], rel=1e-9)


def test_where_the_wastewater_goes():
    """Decision 10 (agreed Nov 10): a combined cycle on wet cooling drawing surface water returns to its source, on wells or a utility's water
    to the sewer; dry, simple cycle, engines and fuel cells to the sewer. The same wastewater, wherever it goes; zero liquid discharge
    evaporates it, so withdrawal is unchanged and consumption takes it."""
    assert gp.default_discharge("cc", "towers", "surface") == "source" and gp.default_discharge("cc", "towers", "ground") == "sewer"
    assert gp.default_discharge("cc", "dry", "surface") == "sewer" and gp.default_discharge("ct", "none", "surface") == "sewer"
    p = _p("cc", "towers")
    h = {d: gp.hourly(500.0, T, TWB, RH, "cc", "towers", p, 2, 300.0, discharge=d) for d in gp.DISCHARGES}
    waste = h["sewer"]["to_sewer"]
    assert waste.sum() > 0
    np.testing.assert_allclose(h["stream"]["to_stream"], waste) and np.testing.assert_allclose(h["source"]["to_source"], waste)
    for d in gp.DISCHARGES:
        np.testing.assert_allclose(h[d]["withdrawn"], h["sewer"]["withdrawn"])
    np.testing.assert_allclose(h["none"]["consumed"], h["sewer"]["consumed"] + waste) and not h["none"]["returned"].any()
    with pytest.raises(ValueError):
        gp.hourly(500.0, T, TWB, RH, "cc", "towers", p, 2, 300.0, discharge="river")
