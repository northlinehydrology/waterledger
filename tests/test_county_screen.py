"""The county screen on a place's utilities (design 0011, step 2): EIA-861's county lists move a utility that doesn't serve the place's county out
of first place, with two guards against the list's own errors. Cases from the Nov 25, 2026 measurement, worked by hand."""
import geopandas as gpd
import shapely

from waterledger_data import energy as en

U = lambda name, eid, share, listed, type_="INVESTOR OWNED": {"name": name, "eia_id": eid, "share": share, "type": type_, "balancing_authority": "X",
                                                              "county_listed": listed}
LOADS = {1: {"customers": 2_000_000}, 2: {"customers": 300_000}, 3: {"customers": 4_000}, 4: {"customers": 50_000}}


def test_a_utility_not_listed_in_the_county_gives_way():
    """DTE drawn over Ada Township by HIFLD, not listed by EIA in Kent County; Consumers is."""
    r = en.ranked([U("DTE", 1, 0.6, False), U("Consumers", 2, 1.0, True)], LOADS)
    assert r[0]["name"] == "Consumers" and [u["name"] for u in r] == ["Consumers", "DTE"]


def test_a_smaller_replacement_does_not_take_first_place():
    """Georgia Power covers Savannah; EIA's list leaves out Chatham County; Canoochee EMC lists it but covers a sliver."""
    r = en.ranked([U("Georgia Power", 1, 1.0, False), U("Canoochee EMC", 3, 0.04, True, "COOPERATIVE")], LOADS)
    assert r[0]["name"] == "Georgia Power"


def test_a_city_utility_is_not_promoted_outside_its_city():
    """The City of Ada (MN) lists Norman County; the townships around it stay with their co-op."""
    place = {"base": "Flom", "km2": 90.0}
    r = en.ranked([U("Wild Rice Electric", 4, 1.0, False, "COOPERATIVE"), U("City of Ada", 3, 1.0, True, "MUNICIPAL"),
                   U("Red River Valley", 2, 1.0, True, "COOPERATIVE")], LOADS, place)
    assert r[0]["name"] == "Red River Valley"


def test_unknown_numbers_are_not_ruled_out():
    """A utility EIA doesn't list in the state at all (a retired number) is unknown, so it isn't screened, and it isn't moved."""
    r = en.ranked([U("Penelec (old number)", 2, 1.0, None), U("Somerset Rural", 3, 0.2, True, "COOPERATIVE")], LOADS)
    assert r[0]["name"] == "Penelec (old number)"


def test_without_marks_nothing_changes():
    us = [{k: v for k, v in u.items() if k != "county_listed"} for u in (U("DTE", 1, 0.6, False), U("Consumers", 2, 1.0, True))]
    assert en.ranked(us, LOADS)[0]["name"] == "DTE"


def test_mark_counties_reads_virginias_independent_cities():
    places = gpd.GeoDataFrame([{"geoid": "5101000", "county": "Alexandria", "county_fips": "51510", "geometry": shapely.Point(0, 0)},
                               {"geoid": "51059", "county": "Fairfax", "county_fips": "51059", "geometry": shapely.Point(0, 0)}], crs=4326)
    by = {"5101000": [{"eia_id": 9, "name": "Dominion"}, {"eia_id": 7, "name": "Gone"}], "51059": [{"eia_id": 9, "name": "Dominion"}]}
    lists = {9: {"alexandriacity", "fairfax"}, 5: {"fairfaxcity"}}
    out = en.mark_counties("VA", by, places, lists)
    assert out["5101000"][0]["county_listed"] is True and out["5101000"][1]["county_listed"] is None
    assert out["51059"][0]["county_listed"] is True
