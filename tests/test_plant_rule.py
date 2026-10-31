"""One rule for a place's own sewer plant, in every state: its name, and close."""
from waterledger_data import wastewater as ww


def plant(city, km, design=5.0):
    return {"id": city, "name": city, "city": city, "lat": km / 111.2, "lon": 0.0, "design_mgd": design}


def test_own_needs_the_name_and_the_distance():
    assert ww.is_own(True, 9) and ww.is_own(True, ww.OWN_KM)
    assert not ww.is_own(True, 35) and not ww.is_own(False, 1)


def test_own_comes_first_and_small_plants_only_if_own():
    rows = [plant("Far", 30), plant("Close", 8), plant("Near", 3), plant("Tiny", 2, 0.1)]
    assert [q["id"] for q in ww.nearest(rows, 0, 0, "Close")] == ["Close", "Near", "Far"]
    assert [q["id"] for q in ww.nearest(rows, 0, 0, "Far")] == ["Near", "Close", "Far"]
    assert [q["id"] for q in ww.nearest(rows, 0, 0, "Tiny")] == ["Tiny", "Near", "Close", "Far"]
