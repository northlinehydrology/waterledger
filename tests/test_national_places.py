"""The national tier's places (Census) for the test states: Ohio, Virginia and Texas (nightly; pytest -m live)."""
import pytest

import waterledger as wl

pytestmark = pytest.mark.live


@pytest.mark.parametrize("query, geoid, name, kind, county", [
    ("Columbus city, OH", "3918000", "Columbus", "city", "Franklin"),
    ("Austintown township, OH", "3909903198", "Austintown Township", "township", "Mahoning"),
    ("Loudoun County, VA", "51107", "Loudoun County", "county", "Loudoun"),
    ("Ashburn, VA", None, None, None, None),
    ("Richmond city, VA", "5167000", "Richmond", "city", "Richmond"),
    ("Austin city, TX", "4805000", "Austin", "city", "Travis"),
    ("Abilene city, TX", "4801000", "Abilene", "city", "Taylor"),
])
def test_finds(query, geoid, name, kind, county):
    if geoid is None:                     # Ashburn is a census-designated place, not a government: look up Loudoun County
        with pytest.raises(KeyError):
            wl.place(query)
        return
    p = wl.place(query)
    assert (p.geoid, p.name, p.kind, p.county) == (geoid, name, kind, county)
    assert wl.place(geoid=geoid) == p


def test_counts_and_independent_cities_once():
    from waterledger_data import census
    va = census.places("51")
    assert (va.level == "county").sum() == 95 and (va.name == "Richmond city").sum() == 1
    oh = census.places("39")
    assert (oh.level == "township").sum() > 1300 and oh.county.notna().all()
