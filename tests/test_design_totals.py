"""Design totals (design 0020, proposal 1; 3.25.0): Site.by_design's DesignTotals equal the cell records and the estimates for every design and cooling
plant: campus water as est.water counts it, electricity as est.electricity, power-plant water as est.grid_water (the balancing authority's hourly mix) and
est.power_plants (the site's power option), and the differences against towers worked from them. On the snapshots stored on this machine, Michigan's
site data and Ohio's and Virginia's national-tier snapshots; a state whose snapshot isn't stored is skipped."""
from types import SimpleNamespace

import pytest

import waterledger as wl
from waterledger import comparisons as cm
from waterledger import scenario as sc
from waterledger.estimate import Electricity, GridWater, Range

DESIGNS = ("dry", "assist", "hybrid", "towers")
PLANTS = ("shared", "warm", "chilled")
MW = 300
PLACES = ["Gaines charter township, MI", "Columbus city, OH", "Loudoun County, VA"]


def _record(place, design, plant):
    """The cell's (Michigan: the place's cell or region's) per-100 MW results for a design and plant, and the D they sit in, as the providers read them."""
    if place.state == "MI":
        D, region = sc.cooling(sc.place(place.geoid), sc.data("estimates"), plant)
    else:
        from waterledger.national.data import state_data
        from waterledger.national.provider import _cooling
        region, runs = _cooling(place.state, place)
        D = {"regions": {region: sc.for_plant(runs[region], plant)}, "staff": {"runs": state_data(place.state).staff_runs()}}
    return D, region, D["regions"][region]["per_100mw"][design]


def _band(r):
    return (r.p10, r.p50, r.p90)


def _scaled(stat):
    return pytest.approx((stat["p10"] * MW / 100, stat["p50"] * MW / 100, stat["p90"] * MW / 100), rel=1e-12)


@pytest.fixture(scope="module", params=PLACES)
def case(request):
    try:
        p = wl.place(request.param)
        site = wl.Site(place=p, facility=wl.DataCenter(it_mw=MW, cooling="assist"))
        cmp = site.by_design(plants=PLANTS)
    except Exception as e:                          # noqa: BLE001  no stored snapshot for the state on this machine
        pytest.skip(f"{request.param}: {type(e).__name__}: {e}")
    return site, cmp


def test_every_plant_and_design_is_there(case):
    site, cmp = case
    assert set(cmp.plants) == set(PLANTS) and all(list(t) == list(DESIGNS) for t in cmp.plants.values())
    assert cmp.designs == cmp.plants["shared"] and cmp.reference == "towers"
    assert all(d.plant == p and d.reference == "towers" for p, t in cmp.plants.items() for d in t.values())


def test_totals_equal_the_estimates(case):
    site, cmp = case
    for plant, table in cmp.plants.items():
        for k, d in table.items():
            est = site.model_copy(update={"facility": site.facility.model_copy(update={"cooling": k, "plant": plant})}).estimate()
            assert d.evaporated == est.water.consumed.avg and d.evaporated_peak_day == est.water.consumed.peak_day
            e = est.electricity
            assert (d.avg_mw, d.peak_mw, d.peak_day_mw) == (e.avg_mw, e.peak_mw, e.peak_day_mw)
            assert _band(d.annual_mwh) == pytest.approx(tuple(x * 8760 for x in _band(e.avg_mw)), rel=1e-12)
            g = est.grid_water
            assert g is not None and cmp.balancing_authority == g.balancing_authority
            assert (d.grid_water, d.grid_water_peak_day) == (g.consumed, g.consumed_peak_day)
            assert d.at_power_plants == est.power_plants[est.site.power].consumed
            o = est.power_plants[est.site.power]
            assert d.at_power_plants_peak_day.p50 == pytest.approx(o.consumed.p50 * e.peak_day_mw.p50 / e.avg_mw.p50, rel=1e-12)


def test_totals_equal_the_cell_records(case):
    site, cmp = case
    for plant, table in cmp.plants.items():
        for k, d in table.items():
            D, region, r = _record(site.place, k, plant)
            assert _band(d.avg_mw) == _scaled(r["power_mw_avg"]) and _band(d.peak_mw) == _scaled(r["power_mw_peak_1in10"])
            assert _band(d.peak_day_mw) == _scaled(r["power_mw_peak_day_1in10"])
            ba = cmp.balancing_authority
            assert _band(d.grid_water) == _scaled(r[f"grid_{ba}_consumed_avg"]) and _band(d.grid_water_peak_day) == _scaled(r[f"grid_{ba}_consumed_peak_1in10"])
            # campus water: withdrawn + condensate - returned on the middle estimate, staff water included (scenario.cooling_estimate)
            F = lambda key: sc.flow(D, region, k, key, MW)["mid"]
            cond = lambda key: r[key]["p50"] * MW / 100 if key in r else 0.0
            assert d.evaporated.p50 == pytest.approx(max(0.0, F("withdrawn_avg") + cond("condensate_avg") - F("returned_avg")), rel=1e-12)
            assert d.evaporated_peak_day.p50 == pytest.approx(max(0.0, F("withdrawn_peak_1in10") + cond("condensate_peak_1in10") - F("returned_peak_1in10")), rel=1e-12)


def test_differences_against_towers(case):
    site, cmp = case
    for table in cmp.plants.values():
        t = table["towers"]
        assert (t.more_electricity_pct, t.more_peak_mw, t.saves_on_site, t.extra_grid_water, t.extra_plant_water) == (0, 0, 0, 0, 0)
        for d in table.values():
            assert d.more_electricity_pct == pytest.approx(100 * (d.annual_mwh.p50 / t.annual_mwh.p50 - 1), rel=1e-9)
            assert d.more_peak_mw == pytest.approx(d.peak_mw.p50 - t.peak_mw.p50) and d.saves_on_site == pytest.approx(t.evaporated.p50 - d.evaporated.p50)
            assert d.extra_grid_water_share == pytest.approx(100 * (d.grid_water.p50 - t.grid_water.p50) / t.evaporated.p50)
            assert d.extra_plant_water_share == pytest.approx(100 * (d.at_power_plants.p50 - t.at_power_plants.p50) / t.evaporated.p50)
        assert table["dry"].more_electricity_pct > 0 and table["dry"].saves_on_site > 0        # dry trades the towers' water for electricity
    assert cmp.best == min(cmp.designs, key=lambda k: cmp.designs[k].total)
    assert cmp.best_hourly_grid == min(cmp.designs, key=lambda k: cmp.designs[k].evaporated.p50 + cmp.designs[k].grid_water.p50)


def test_old_callers_keep_their_answer(case):
    """3.24 callers: designs without pads, no plants, and the fields they read unchanged."""
    site, cmp = case
    old = site.by_design(("dry", "hybrid", "towers"))
    assert list(old.designs) == ["dry", "hybrid", "towers"] and old.plants == {"shared": old.designs}
    for k in old.designs:
        a, b = old.designs[k], cmp.designs[k]
        assert (a.evaporated, a.at_power_plants, a.avg_mw, a.peak_mw) == (b.evaporated, b.at_power_plants, b.avg_mw, b.peak_mw)
    assert old.closed_loop_more_power_pct == cmp.closed_loop_more_power_pct and old.closed_loop_saves_on_site == cmp.closed_loop_saves_on_site


# on made-up numbers: a 3.24 call (no grid water) still works, and a reference outside the designs leaves the differences empty

R = lambda x: Range(p10=x, p50=x, p90=x)
OPTS = {"mix": {"label": "Mix", "gal_mwh": 200, "lo": 150, "hi": 250}}


def _design(c, mw, peak, g=None):
    water = SimpleNamespace(consumed=SimpleNamespace(avg=R(c)))
    e = Electricity(avg_mw=R(mw), peak_mw=R(peak), peak_day_mw=R(mw * 1.1))
    grid = None if g is None else GridWater(balancing_authority="MISO", **{k: R(g) for k in ("consumed", "withdrawn", "consumed_peak_day", "withdrawn_peak_day", "marginal_consumed",
                                                                                              "marginal_withdrawn", "marginal_consumed_peak_day", "marginal_withdrawn_peak_day")})
    return (water, e) if g is None else (water, e, grid)


def test_compare_designs_on_made_up_numbers():
    d = cm.compare_designs({"dry": _design(0.0, 110, 150, 1.1), "towers": _design(1.0, 100, 120, 1.0)}, OPTS, "mix", "mix")
    dry = d.designs["dry"]
    assert dry.more_electricity_pct == pytest.approx(10) and dry.more_peak_mw == 30 and dry.saves_on_site == 1.0
    assert dry.extra_grid_water == pytest.approx(0.1) and dry.extra_grid_water_share == pytest.approx(10)
    assert dry.extra_plant_water == pytest.approx(cm.plant_water(10, 200)) and dry.evaporated_peak_day is None
    assert d.best_hourly_grid == "dry" and d.balancing_authority == "MISO"
    old = cm.compare_designs({"dry": _design(0.0, 110, 150), "towers": _design(1.0, 100, 120)}, OPTS, "mix", "mix")
    assert old.designs["dry"].grid_water is None and old.designs["dry"].extra_grid_water is None and old.best_hourly_grid is None
    assert old.designs["dry"].more_electricity_pct == pytest.approx(10)
    none = cm.compare_designs({"dry": _design(0.0, 110, 150)}, OPTS, "mix", "mix")
    assert none.reference is None and none.designs["dry"].more_electricity_pct is None
    zero = cm.compare_designs({"dry": _design(0.0, 110, 150, 1.1), "towers": _design(0.0, 100, 120, 1.0)}, OPTS, "mix", "mix", reference="dry")
    assert zero.designs["towers"].extra_grid_water_share is None        # a share of no water means nothing
