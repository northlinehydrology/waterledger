"""wl.place finds Michigan places by name or Census GEOID (from the local site, or the files waterledger.org publishes)."""
import pytest

import waterledger as wl


def test_by_name_and_geoid():
    p = wl.place("Gaines charter township, MI")
    assert (p.geoid, p.name, p.county, p.state) == ("2608131240", "Gaines Charter Township", "Kent", "MI")
    assert 42 < p.lat < 43 and -86 < p.lon < -85
    assert wl.place(geoid="2608131240") == p == wl.place("gaines charter", state="MI", county="Kent")
    assert wl.Place.model_validate_json(p.model_dump_json()) == p


def test_other_states_say_so():
    with pytest.raises(NotImplementedError, match="national tier"):
        wl.place("Columbus city, OH")
    with pytest.raises(ValueError, match="state"):
        wl.place("Gaines charter township")
