"""Rainfall and storms cover every county and independent city, and NOAA's rate limit does not lose a county."""
import io, json, urllib.error

import pandas as pd
import pytest

from waterledger.national import climate as nc
from waterledger_data import census, divisions


def test_independent_cities_get_rain_and_storms(monkeypatch):
    pl = pd.DataFrame({"geoid": ["51059", "5167000", "5121088", "5121000"], "level": ["county", "place", "place", "place"],
                       "county_fips": ["51059", "51760", "51059", "51760"], "lat": [38.8, 37.5, 38.9, 37.6], "lon": [-77.3, -77.5, -77.2, -77.4]})
    monkeypatch.setattr(census, "places", lambda fips: pl)
    assert [c["geoid"] for c in nc.climate_areas("VA")] == ["51059", "51760"]
    assert [c["geoid"] for c in nc.counties("VA")] == ["51059"]         # cooling stations stay on counties


def _busy():
    return urllib.error.HTTPError("u", 429, "Too Many Requests", {}, None)


def test_cag_waits_out_the_rate_limit(monkeypatch):
    answers = [_busy(), _busy(), io.BytesIO(json.dumps({"ok": 1}).encode())]

    def urlopen(req, timeout):
        a = answers.pop(0)
        if isinstance(a, Exception):
            raise a
        return a
    waits = []
    monkeypatch.setattr(divisions.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(divisions.time, "sleep", waits.append)
    assert divisions.cag_json("https://noaa.test") == {"ok": 1}
    assert waits == [30, 60]


def test_a_refused_county_fails_the_build(monkeypatch, tmp_path):
    def urlopen(req, timeout):
        raise _busy()
    monkeypatch.setattr(divisions.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(divisions.time, "sleep", lambda s: None)
    monkeypatch.setattr(divisions, "_cached", lambda name, fn: fn())
    with pytest.raises(urllib.error.HTTPError):
        divisions.rain_in("VA", [{"geoid": "51760", "lat": 37.5, "lon": -77.5}])
