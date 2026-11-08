"""One state end to end, for any state, with nothing hand-listed and no other state's data: places, context, an estimate for every design, the rules on lake water.

    WATERLEDGER_TEST_STATE=OH uv run pytest -m live tests/test_state_end_to_end.py

build-state runs it for the state it just built (WATERLEDGER_DATA=live); with no such setting it reads the published snapshot."""
import json
import os
import random

import pytest

import waterledger as wl
from waterledger import states

STATE = os.environ.get("WATERLEDGER_TEST_STATE", "").upper()
pytestmark = [pytest.mark.live, pytest.mark.skipif(not STATE, reason="WATERLEDGER_TEST_STATE not set")]
DESIGNS = ("dry", "assist", "hybrid", "towers")
SAMPLE = 4


@pytest.fixture(scope="module")
def provider():
    return states.provider(STATE)


@pytest.fixture(scope="module")
def places(provider):
    """A few places, the same each run: one of each kind the state has, up to SAMPLE."""
    ids = sorted(provider.geoids())
    assert ids, f"{STATE} has no places"
    by_kind = {}
    for g in random.Random(1).sample(ids, min(40, len(ids))):
        p = wl.place(geoid=g)
        by_kind.setdefault(p.kind, p)
    return list(by_kind.values())[:SAMPLE]


def test_a_place_knows_its_state_and_context(places):
    for p in places:
        assert p.state == STATE and p.county_fips and str(p.geoid).startswith(next(f for f, s in states.FIPS.items() if s == STATE))
        c = p.context()
        assert c.jurisdiction.state == STATE and c.climate.station and c.energy.power_plant_water is not None
        assert c.climate.rain_in is None or 3 < c.climate.rain_in < 200
        assert set(c.climate.design_storms_in) == {"2", "10", "100"}
        assert c.supply.county_water_use_usgs is None or c.supply.county_water_use_usgs.source == "usgs_wu2015"
        if c.supply.nearest_system_km is not None:
            assert c.supply.nearest_system_km >= 0 and c.supply.nearest_system.population > 3300
        assert all(q.km <= 40 for q in c.wastewater.plants) and len(c.wastewater.plants) <= 10


def test_what_a_state_lacks_is_labeled_not_silently_empty(places):
    for p in places:
        c = p.context()
        if not c.jurisdiction.rules:
            assert "rules" in c.jurisdiction.not_covered
        if STATE != "MI":
            assert c.supply.household_wells is None and "household_wells" in c.supply.not_covered
            assert "coldwater_streams" in c.receiving.not_covered


@pytest.mark.parametrize("cooling", DESIGNS)
def test_an_estimate_runs_and_closes(places, cooling):
    for p in places:
        e = wl.Site(place=p, facility=wl.DataCenter(it_mw=100, cooling=cooling)).estimate()
        w = e.water
        assert e.site.source in ("muni", "wells") and e.site.wastewater and e.site.acres and e.site.land_before
        assert w.withdrawn.peak_day.p50 >= w.withdrawn.avg.p50 > 0
        if w.condensate:
            assert w.withdrawn.avg.p50 + w.condensate.avg.p50 == pytest.approx(w.consumed.avg.p50 + w.returned.avg.p50, rel=1e-9)
        assert e.electricity.avg_mw.p50 > 0 and e.equivalents.golf_courses is not None
        pd = e.electricity.peak_day_mw                                    # model 1.9: the peak day's average power, between the two
        assert pd is not None and e.electricity.avg_mw.p50 < pd.p50 < e.electricity.peak_mw.p50 and pd.p10 <= pd.p50 <= pd.p90
        assert e.site.power in e.power_plants
        json.loads(e.model_dump_json())


def test_reference_values_are_this_states_and_labeled(provider, places):
    r = provider.reference(places[0])
    assert r["power"] in r["power_options"] and r["golf_gpd"] > 0 and r["golf_note"] and r["golf_basis"]
    assert "state_mix" in r["power_options"]


def test_lake_water_follows_the_shoreline(provider, places):
    shore = set(provider.shore_geoids())
    inland = next((p for p in places if p.geoid not in shore), None)
    if inland:
        assert inland.context().receiving.great_lake is None
        with pytest.raises(ValueError, match="Great Lake"):
            wl.Site(place=inland, facility=wl.DataCenter(it_mw=100, cooling="towers"), source="lake").estimate()
        with pytest.raises(ValueError, match="Great Lake"):
            wl.Site(place=inland, facility=wl.DataCenter(it_mw=100, cooling="lake"), source="lake").estimate()
    if shore:
        p = wl.place(geoid=sorted(shore)[0])
        assert p.context().receiving.great_lake
        e = wl.Site(place=p, facility=wl.DataCenter(it_mw=100, cooling="lake"), source="lake").estimate()
        assert e.water.lake_source and e.water.withdrawn.avg.p50 == e.water.returned.avg.p50 and "great_lakes" in e.levels
