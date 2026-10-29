"""wl.place finds Michigan places by name or Census GEOID (from the local site, or the files waterledger.org publishes)."""
import pytest

import waterledger as wl


def test_by_name_and_geoid():
    p = wl.place("Gaines charter township, MI")
    assert (p.geoid, p.name, p.county, p.state) == ("2608131240", "Gaines Charter Township", "Kent", "MI")
    assert 42 < p.lat < 43 and -86 < p.lon < -85
    assert wl.place(geoid="2608131240") == p == wl.place("gaines charter", state="MI", county="Kent")
    assert wl.Place.model_validate_json(p.model_dump_json()) == p


def test_other_states_go_to_the_national_tier():
    assert repr(wl.states.provider("OH")) == "Provider(OH: national)"
    assert repr(wl.states.provider("mi")) == "Provider(MI: own and national)"
    with pytest.raises(NotImplementedError, match="OH: the national tier's context"):
        wl.states.provider("OH").context(None)
    with pytest.raises(KeyError):
        wl.states.provider("XX")
    with pytest.raises(ValueError, match="state"):
        wl.place("Gaines charter township")
