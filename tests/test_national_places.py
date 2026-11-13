"""The national tier's places (Census) for the test states: Ohio, Virginia, Texas, Wisconsin, Indiana, Pennsylvania, Minnesota, Georgia, Illinois, Arizona and New York (nightly; pytest -m live)."""
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
    ("Madison city, WI", "5548000", "Madison", "city", "Dane"),
    ("Mount Pleasant village, WI", "5554875", "Mount Pleasant", "village", "Racine"),
    ("Lebanon city, IN", "1842624", "Lebanon", "city", "Boone"),
    ("Indianapolis city (balance), IN", "1836003", "Indianapolis", "city", "Marion"),   # a consolidated city's balance (FUNCSTAT F)
    ("Pittsburgh city, PA", "4261000", "Pittsburgh", "city", "Allegheny"),
    ("Archbald borough, PA", "4202832", "Archbald", "borough", "Lackawanna"),
    ("Hazle township, PA", "4207933376", "Hazle Township", "township", "Luzerne"),
    ("Minneapolis city, MN", "2743000", "Minneapolis", "city", "Hennepin"),
    ("Farmington city, MN", "2720618", "Farmington", "city", "Dakota"),
    ("Fayetteville city, GA", "1328968", "Fayetteville", "city", "Fayette"),
    ("Atlanta city, GA", "1304000", "Atlanta", "city", "Fulton"),
    ("Aurora city, IL", "1703012", "Aurora", "city", "Kane"),
    ("Chicago city, IL", "1714000", "Chicago", "city", "Cook"),
    ("Elk Grove Village village, IL", "1723256", "Elk Grove Village", "village", "Cook"),
    ("Mesa city, AZ", "0446000", "Mesa", "city", "Maricopa"),
    ("Marana town, AZ", "0444270", "Marana", "town", "Pima"),
    ("Apache County, AZ", "04001", "Apache County", "county", "Apache"),
    ("Buffalo city, NY", "3611000", "Buffalo", "city", "Erie"),
    ("Hamburg town, NY", "3602931654", "Hamburg Town", "town", "Erie"),    # a town: New York's governing subdivision
    ("Hamburg village, NY", "3631643", "Hamburg", "village", "Erie"),      # a village inside that town
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


@pytest.mark.parametrize("state, lat, lon, name", [
    ("OH", 39.997, -82.998, "Columbus"),               # downtown Columbus
    ("VA", 39.0438, -77.4874, "Loudoun County"),       # Ashburn data center alley: unincorporated Loudoun County
    ("TX", 30.2672, -97.7431, "Austin"),
    ("OH", 41.0947, -80.7608, "Austintown Township"),  # outside any village: the township governs
    ("WI", 43.0747, -89.3841, "Madison"),              # the Wisconsin Capitol
    ("IN", 39.7684, -86.1581, "Indianapolis"),         # downtown Indianapolis: the consolidated city's balance
    ("PA", 40.4406, -79.9959, "Pittsburgh"),           # downtown Pittsburgh
    ("MN", 44.9778, -93.2650, "Minneapolis"),          # downtown Minneapolis
    ("GA", 33.7490, -84.3880, "Atlanta"),              # downtown Atlanta
    ("IL", 41.8781, -87.6298, "Chicago"),              # the Loop
    ("AZ", 33.4484, -112.0740, "Phoenix"),             # downtown Phoenix
    ("NY", 42.8864, -78.8784, "Buffalo"),              # downtown Buffalo
])
def test_place_at_a_point(state, lat, lon, name):
    p = wl.place(lat=lat, lon=lon)
    assert (p.name, p.state) == (name, state)


@pytest.mark.parametrize("lat, lon, name", [(42.805, -85.604, "Gaines Charter Township"), (42.4734, -83.2219, "Southfield")])
def test_michigan_point_lookup_uses_michigan_places(lat, lon, name):
    p = wl.place(lat=lat, lon=lon)
    assert p.name == name and len(p.geoid) == 10
