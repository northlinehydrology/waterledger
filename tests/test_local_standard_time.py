"""Local standard time at any place, on values worked by hand."""
import numpy as np
import pytest

from waterledger_data import climate
from waterledger_models.weather import local_standard_offset, open_meteo_local_standard, to_local_standard


@pytest.mark.parametrize("lon,hours", [(-85.5, -6), (-83.0, -6), (-77.5, -5), (-99.9, -7), (-157.8, -11)])
def test_local_standard_offset(lon, hours):
    assert local_standard_offset(lon) == hours    # lon / 15, rounded: the rule the station records use


def test_utc_moved_to_local_standard_and_trimmed_to_whole_days():
    times = [str(x)[:16] for x in np.arange(np.datetime64("1999-12-31T00:00"), np.datetime64("2000-01-03T00:00"), np.timedelta64(1, "h"))]
    payload = {"hourly": {"time": times, "temperature_2m": list(range(len(times))), "relative_humidity_2m": list(range(len(times)))}}
    out = open_meteo_local_standard(payload, -85.5, "2000-01-01", "2000-01-01")["hourly"]    # UTC-6
    assert out["time"][0] == "2000-01-01T00:00" and out["time"][-1] == "2000-01-01T23:00" and len(out["time"]) == 24
    assert out["temperature_2m"][0] == 30          # 06:00 UTC on Jan 1 is hour 30 from 00:00 UTC on Dec 31
    assert to_local_standard(["2000-01-01T06:00"], -85.5)[0] == ["2000-01-01T00:00"]


def test_hourly_weather_is_local_standard_for_any_place(tmp_path, monkeypatch):
    """Asked for in UTC whatever the place; no time zone is named in the request."""
    import json
    times = [str(x)[:16] for x in np.arange(np.datetime64("1999-12-31T00:00"), np.datetime64("2000-01-03T00:00"), np.timedelta64(1, "h"))]
    seen = {}

    def fake_fetch(url, path):
        seen["url"] = url
        json.dump({"hourly": {"time": times, "temperature_2m": list(range(len(times))), "relative_humidity_2m": list(range(len(times)))}}, open(tmp_path / "f.json", "w"))
        return tmp_path / "f.json"
    monkeypatch.setattr(climate, "_fetch", fake_fetch)
    t, T, RH = climate.hourly_weather(30.27, -97.74, "2000-01-01", "2000-01-01", "austin")     # -97.74 / 15 = -6.5, rounds to -7
    assert "timezone=GMT" in seen["url"] and "Detroit" not in seen["url"] and "start_date=1999-12-31" in seen["url"]
    assert t[0] == "2000-01-01T00:00" and len(t) == 24 and T[0] == 31                          # 07:00 UTC on Jan 1 is hour 31
