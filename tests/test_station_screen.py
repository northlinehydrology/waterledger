"""The station screens, on values worked by hand."""
import numpy as np
import pandas as pd
import pytest

from waterledger_data import climate


def _series(years=(2000, 2001, 2002)):
    """Hourly temperature with a plain daily cycle, 20 C to 30 C, the same every day."""
    idx = pd.date_range(f"{years[0]}-01-01", f"{years[-1]}-12-31 23:00", freq="h")
    return pd.Series(25 + 5 * np.sin(2 * np.pi * idx.hour / 24), index=idx, name="T")


def test_poor_years():
    idx = pd.date_range("2000-01-01", "2002-12-31 23:00", freq="h")
    seen = pd.Series(True, index=idx)
    seen[idx.year == 2001] = False                              # 2001: nothing observed
    seen[(idx.year == 2002) & (idx.day_of_year > 311)] = False    # 2002: 311 / 365 = 85.2%, in
    assert climate.poor_years(seen) == [2001]
    seen[(idx.year == 2002) & (idx.day_of_year > 310)] = False    # 310 / 365 = 84.9%, out
    assert climate.poor_years(seen) == [2001, 2002]


def test_fort_worth_like_reading_is_suspect_and_a_real_warm_hour_is_not():
    T = _series()
    # hour 5 is 25 + 5 sin(2 pi 5/24) = 29.83 at every day of the month, so its 99th percentile is 29.83; the margin puts the line at 39.83
    t = pd.Timestamp("2001-08-05 05:00")
    T[t] = 39.8
    assert not climate.suspect_temperatures(T)[pd.Timestamp("2001-08-05 12:00")]
    T[t] = 53.9
    assert climate.suspect_temperatures(T)[t]


def test_one_hour_spike_either_way():
    T = pd.Series([20.0, 20.0, 29.0, 20.0, 20.0, 11.5, 20.0, 20.0, 27.0, 20.0], index=pd.date_range("2000-01-01", periods=10, freq="h"))
    s = climate._spikes(T, climate.STEP_C)
    assert list(T.index[s].hour) == [2, 5]                      # +9 and -8.5 from both sides; +7 at hour 8 is not


def test_a_step_is_not_a_spike():
    T = pd.Series([35.0, 35.0, 22.0, 22.0], index=pd.date_range("2000-06-01", periods=4, freq="h"))   # a front comes through and stays
    assert not climate._spikes(T, climate.STEP_C).any()


def test_a_neighbor_keeps_a_real_record_and_exposes_a_fault():
    T = _series()
    t = pd.Timestamp("2001-06-28 12:00")
    T[t] = 46.7
    suspect = climate.suspect_temperatures(T)
    assert suspect[t]
    agree = pd.DataFrame({"T": 46.7 - climate.NEIGHBOR_C}, index=[t])      # the same heat 8 C lower at the next airport
    assert t not in climate.unconfirmed(T, suspect, [agree])
    differ = pd.DataFrame({"T": 46.7 - climate.NEIGHBOR_C - 0.1}, index=[t])
    assert t in climate.unconfirmed(T, suspect, [differ])
    assert t in climate.unconfirmed(T, suspect, [])                        # nobody to back it up: it goes
    near = pd.DataFrame({"T": 45.0}, index=[t + pd.Timedelta(hours=1)])    # the hour beside counts, as reports fall on different minutes
    assert t not in climate.unconfirmed(T, suspect, [near])


def test_isd_hourly_leaves_out_poor_years_and_bad_hours(monkeypatch):
    idx = pd.date_range("2000-01-01", "2002-12-31 23:00", freq="h")
    T = _series()
    bad = pd.Timestamp("2000-07-04 05:00")
    T[bad] = 53.9
    raw = pd.DataFrame({"T": T, "Td": T - 10})
    raw = raw[~((raw.index.year == 2001) & (raw.index.day_of_year > 7))]     # 2001: a week observed
    monkeypatch.setattr(climate, "_isd_frame", lambda s, y: raw)
    # lon 0: local standard time is UTC, so the hours are as written
    got = climate.isd_hourly({"id": "1-2", "lat": 40.0, "lon": 0.0}, 2000, 2002, min_share=0.5, neighbors=lambda years: [])
    times, temps, rh, share, screen = got
    assert screen == {"years_left_out": [2001], "hours_removed": 1, "dew_points_removed": 0}
    assert share == pytest.approx(len(raw) / len(idx))
    assert not any(t.startswith("2001") for t in times) and len(times) == 8784 + 8760          # 2000 is a leap year
    assert max(temps) == pytest.approx(30.0)
    i = times.index("2000-07-04T05:00")
    # filled from the hours beside it: 25 + 5 sin(2 pi 4/24) = 29.33 and 25 + 5 sin(2 pi 6/24) = 30, so 29.665
    assert temps[i] == pytest.approx((25 + 5 * np.sin(2 * np.pi * 4 / 24) + 30) / 2)
