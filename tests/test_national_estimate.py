"""Climate and site.estimate() from the national tier for the test states (nightly; pytest -m live)."""
import pytest

import waterledger as wl

pytestmark = pytest.mark.live


@pytest.mark.parametrize("query", ["Columbus city, OH", "Loudoun County, VA", "Austin city, TX"])
def test_climate(query):
    c = wl.place(query).context().climate
    assert c.provider == "national" and c.station and set(c.design_storms_in) == {"2", "10", "100"} and 20 < c.rain_in < 60


@pytest.mark.parametrize("query", ["Columbus city, OH", "Loudoun County, VA", "Austin city, TX"])
def test_estimate_orders_designs(query):
    p = wl.place(query)
    est = {cool: wl.Site(place=p, facility=wl.DataCenter(it_mw=300, cooling=cool)).estimate() for cool in ("dry", "assist", "hybrid", "towers")}
    avg = {k: e.water.withdrawn.avg.p50 for k, e in est.items()}
    assert avg["dry"] < avg["assist"] < avg["hybrid"] < avg["towers"]          # more evaporation, more water
    t = est["towers"].water
    assert t.withdrawn.peak_day.p50 > t.withdrawn.avg.p50 and t.consumed.avg.p50 < t.withdrawn.avg.p50
    assert est["dry"].site.source in ("muni", "wells") and est["dry"].model_version == wl.models.MODEL_VERSION


def test_hotter_climate_uses_more_water_with_towers():
    tw = lambda q: wl.Site(place=wl.place(q), facility=wl.DataCenter(it_mw=100, cooling="towers")).estimate().water.consumed.avg.p50
    assert tw("Austin city, TX") > tw("Columbus city, OH")


def test_lake_source_is_great_lakes_only():
    with pytest.raises(ValueError, match="Great Lakes"):
        wl.Site(place=wl.place("Austin city, TX"), facility=wl.DataCenter(it_mw=100, cooling="lake")).estimate()
