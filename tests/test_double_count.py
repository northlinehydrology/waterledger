"""Nothing counted twice (Andrew, Nov 17, 2026): the natural yield below a developed site's pervious share leaves out what its surface runoff already carries,
cooling phosphorus is worked on blowdown alone, and the fleet checks add curtailment back so a supply scenario counts it once."""
import importlib.util
import json
import os

import pytest

from waterledger import scenario
from waterledger_models import runoff
from waterledger_models.datacenter import cooling
from waterledger_models.supply import pv, wind

HERE = os.path.dirname(__file__)
Y = runoff.PARAMS["nutrient_yield"]


@pytest.mark.parametrize("k", ["tp", "tn"])
@pytest.mark.parametrize("rain", [10.0, 32.0, 60.0])
def test_natural_yield_split_into_surface_and_below(k, rain):
    """Natural land's surface runoff x the basins' concentration, plus what's left below, is the whole natural yield: split, not added."""
    surface = runoff.LB * runoff.runoff_in(rain, 0.0, "woods") * Y["natural_surface_mg_l"][k]
    for total, below in zip(Y["natural"][k], runoff.natural_below(k, rain)):
        assert below == pytest.approx(max(total - surface, 0.0)) and 0.0 <= below <= total


def test_developed_site_adds_only_the_below_ground_part():
    """After building, the whole site's runoff carries the pervious surface; below it only natural_below is added (not the whole natural yield)."""
    acres, rain, imp = 200.0, 32.0, 0.5
    L = runoff.loads(acres, rain, "farm", imp=imp)
    for k, unit in (("tp", "tp_lb"), ("tn", "tn_lb")):
        emc = runoff.PARAMS["emc"]["developed"][k]
        surface = [runoff.LB * acres * runoff.runoff_in(rain, imp) * e for e in emc]
        below = [acres * (1 - imp) * x for x in runoff.natural_below(k, rain)]
        assert L[unit]["after"] == pytest.approx([s + b for s, b in zip(surface, below)])
        assert all(b < acres * (1 - imp) * x for b, x in zip(below, Y["natural"][k]))


def _golden_estimate(design):
    g = json.load(open(os.path.join(HERE, "data", "golden_cooling.json"), encoding="utf-8"))
    D = {"regions": {"r": {"per_100mw": g["per_100mw"]}}, "staff": {"runs": cooling.staff_runs(40)}}
    return scenario.cooling_estimate(D, "r", design, 300.0, "sewer"), D


@pytest.mark.parametrize("design", ["towers", "hybrid", "assist", "dry"])
def test_blowdown_is_returned_water_less_condensate_and_staff(design):
    """On the middle estimate returned = blowdown + condensate + staff and maintenance water returned: each once, and blowdown carries neither of the others."""
    E, D = _golden_estimate(design)
    staff = cooling.staff_q(D["staff"]["runs"], 300.0)["returned"]["p50"]
    assert E["rAvg"]["mid"] == pytest.approx(E["blowAvg"]["mid"] + E["condAvg"]["mid"] + staff, rel=1e-9)
    assert 0.0 <= E["blowAvg"]["mid"] <= E["rAvg"]["mid"]


def test_cooling_phosphorus_is_on_blowdown_only():
    from waterledger.estimate import water_use
    from waterledger.facilities.data_center import DataCenter
    E, _ = _golden_estimate("towers")
    w = water_use(E)

    class Est:
        water = w
    assert DataCenter(it_mw=300, cooling="towers").cooling_blowdown(Est) == pytest.approx(E["blowAvg"]["mid"])
    assert DataCenter(it_mw=300, cooling="towers").cooling_blowdown(Est) < w.returned.avg.p50
    assert DataCenter(it_mw=300, cooling="dry").cooling_blowdown(Est) is None


def _check(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, "..", "docs", "methods", "power_supply", f"{name}.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_fleet_checks_add_curtailment_back_once():
    """The checks' delivered generation is raised by each balancing authority's curtailment once, and the scenario's dispatch then counts its own surplus;
    the sampled resource ranges sit inside the curtailment-free state fits (docs/methods/power_supply/pv_check.csv, wind_check.csv)."""
    import csv
    c = _check("curtailment")
    assert set(c.RATES) == {"solar", "wind"} and all(0.0 <= r < 0.2 for v in c.RATES.values() for r in v.values())
    rows = {r["group"]: r for r in csv.DictReader(open(os.path.join(HERE, "..", "docs", "methods", "power_supply", "pv_check.csv"), encoding="utf-8"))}
    states = [float(r["resource_match"]) for g, r in rows.items() if len(g) == 2 and int(r["plants"]) >= 10]
    lo, hi = pv.RANGES["resource"]
    assert min(states) <= lo + 0.01 and hi <= max(states) + 0.01
    rows = {r["group"]: r for r in csv.DictReader(open(os.path.join(HERE, "..", "docs", "methods", "power_supply", "wind_check.csv"), encoding="utf-8"))}
    interior = [float(r["resource_match_110m"]) for g, r in rows.items() if g in ("MN", "WY", "TX", "OK", "IL", "IA", "KS", "ND", "NE", "SD", "MI", "IN", "WI")]
    lo, hi = wind.RANGES["resource"]
    assert min(interior) <= lo + 0.01 and hi <= max(interior) + 0.01
