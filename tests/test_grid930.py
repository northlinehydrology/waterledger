"""EIA-930 headers to fuel classes (design 0008, part 1): both the pre-July-2024 headers and the split ones after,
EIA's typos included. No download."""
import pytest

from waterledger_data import grid930 as g


@pytest.mark.parametrize("header, cls", [
    ("Net Generation (MW) from Coal (Adjusted)", "coal"),
    ("Net Generation (MW) from Natural Gas (Adjusted)", "gas"),
    ("Net Generation (MW) from All Petroleum Products (Adjusted)", "oil"),
    ("Net Generation (MW) from Hydropower and Pumped Storage (Adjusted)", "hydro"),
    ("Net Generation (MW) from Hydropower Excluding Pumped Storage (Adjusted)", "hydro"),
    ("Net Generation (MW) from Pumped Storage  (Adjusted)", "hydro"),
    ("Net Generation (MW) from Solar without Integrated Battery Storage (Adjusted)", "solar"),
    ("Net Generation (MW) from Solar witho Integrated Battery Storage (Adjusted)", "solar"),
    ("Net Generation (MW) from Wind with Integrated Battery Storage (Adjusted)", "wind"),
    ("Net Generation (MW) from Battery Storage (Adjusted)", "storage"),
    ("Net Generation (MW) from Other Energy Storage (Adjusted)", "storage"),
    ("Net Generation (MW) from Unknown Energy Storage (Adjusted)", "storage"),
    ("Net Generation (MW) from Geothermal (Adjusted)", "geothermal"),
    ("Net Generation (MW) from Other Fuel Sources (Adjusted)", "other"),
    ("Net Generation (MW) from Unknown Fuel Sources (Adjusted)", "unknown"),
])
def test_fuel_class(header, cls):
    assert g.fuel_class(header) == cls


@pytest.mark.parametrize("header", ["Net Generation (MW) from Coal", "Net Generation (MW) from Coal (Imputed)",
                                    "Demand (MW) (Adjusted)", "Net Generation (MW) (Adjusted)"])
def test_not_a_fuel_column(header):
    assert g.fuel_class(header) is None


def test_unknown_fuel_word_is_an_error():
    with pytest.raises(ValueError):
        g.fuel_class("Net Generation (MW) from Tidal (Adjusted)")


def test_every_class_listed():
    assert {c for _, c in g._WORDS} == set(g.FUELS)


# --- screening the hours (model 1.17) -----------------------------------------------------------------------------------
import numpy as np


def _ba(n=24 * 60, seed=0):
    """A synthetic BA's hours: coal and gas following a daily load with noise, a flat 30 MW of "other", and solar by day."""
    rng = np.random.default_rng(seed)
    hour = np.arange(n) + 438_000
    load = 3000 + 800 * np.sin(2 * np.pi * (hour % 24 - 8) / 24)
    d = {"hour": hour, **{k: np.full(n, np.nan, dtype="float32") for k in g.FUELS}}
    d["coal"] = (1500 + 0.2 * (load - 3000) + rng.normal(0, 15, n)).astype("float32")
    d["gas"] = (load - 1500 + rng.normal(0, 30, n)).astype("float32")
    d["other"] = (30 + rng.normal(0, 1, n)).astype("float32")
    d["solar"] = np.clip(900 * np.sin(2 * np.pi * (hour % 24 - 6) / 24), 0, None).astype("float32")
    return d


def test_natural_hours_are_kept():
    s = g.screen(_ba())
    assert s["hour_ok"].all() and s["screened"] == {}
    assert s["pair_ok"][1:].all() and not s["pair_ok"][0]


def test_a_one_hour_spike_is_screened():
    """AZPS's "other" at 6,137 MW for one hour on 2019-05-30T23 against about 31 MW."""
    d = _ba()
    d["other"][500] = 6137
    s = g.screen(d)
    assert not s["hour_ok"][500] and s["hour_ok"].sum() == len(d["hour"]) - 1
    assert not s["pair_ok"][500] and not s["pair_ok"][501] and s["screened"] == {"other": 1}


def test_a_two_hour_spike_and_a_dropout_are_screened():
    d = _ba()
    d["gas"][700:702] += 5000              # AZPS 2024-03-07T16-17, two hours
    d["coal"][900] = 0                     # a fleet can't stop and restart in an hour
    s = g.screen(d)
    assert list(np.flatnonzero(~s["hour_ok"])) == [700, 701, 900]


def test_a_gap_is_screened_and_a_class_that_stops_reporting_is_zero():
    """A NaN run with the class generating on both sides is a gap; a class that stops being reported (AZPS nuclear from
    2019-12-04T08) is 0 MW, and the hour it stops is not paired with the hour before."""
    d = _ba()
    d["coal"][300:303] = np.nan
    d["gas"][1000:] = np.nan
    s = g.screen(d)
    assert not s["hour_ok"][300:303].any() and s["hour_ok"][1000:].all()
    assert not s["pair_ok"][1000] and s["pair_ok"][1001:].all()


def test_the_screen_is_set_from_the_data():
    """k = 4 ramps: above every large fleet's natural reversals (0.9-3.4), below the artifacts seen (4.9 and 6.4)."""
    assert g.SPIKE_K == 4.0 and g.SPIKE_HOURS == 3 and g.FLOOR == 0.01


# --- generation counted in two BAs (model 1.17) -------------------------------------------------------------------------
def _cache(tmp_path, monkeypatch, ba, d):
    monkeypatch.setattr(g, "RAW", str(tmp_path))
    (tmp_path / "ba").mkdir(exist_ok=True)
    np.savez_compressed(tmp_path / "ba" / f"{ba}.npz", **d)


def test_a_class_counted_in_two_bas_is_left_out_of_the_copy(tmp_path, monkeypatch):
    """AZPS reported Palo Verde, about 4 GW, as SRP did, until 2019-12-04T07: those hours' nuclear is not AZPS's."""
    d = _ba()
    d["hour"] = np.datetime64("2019-12-01T00", "h").astype(np.int64) + np.arange(len(d["hour"]))
    cut = int(np.flatnonzero(d["hour"] == np.datetime64("2019-12-04T07", "h").astype(np.int64))[0])
    d["nuclear"] = np.full(len(d["hour"]), np.nan, dtype="float32")
    d["nuclear"][:cut + 1] = 3990
    _cache(tmp_path, monkeypatch, "AZPS", d)
    x = g.hourly("AZPS")
    assert np.isnan(x["nuclear"]).all() and x["nuclear"].dtype == d["nuclear"].dtype
    assert np.array_equal(x["coal"], d["coal"])                                        # the other classes are untouched
    assert np.nansum(g.hourly("AZPS", raw=True)["nuclear"]) == 3990 * (cut + 1)        # raw: EIA's own values


def test_only_the_listed_hours_are_left_out(tmp_path, monkeypatch):
    monkeypatch.setattr(g, "DOUBLE_COUNTED", (("XX", "coal", "1970-01-01T05", "1970-01-01T07", "YY", "test"),))
    d = {"hour": np.arange(10), **{k: np.ones(10, dtype="float32") for k in g.FUELS}}
    _cache(tmp_path, monkeypatch, "XX", d)
    assert list(np.flatnonzero(np.isnan(g.hourly("XX")["coal"]))) == [5, 6, 7]
    assert not np.isnan(g.hourly("XX")["gas"]).any()


def test_every_double_count_names_the_ba_holding_the_whole_plant():
    for ba, cls, first, last, holder, why in g.DOUBLE_COUNTED:
        assert cls in g.FUELS and holder != ba and len(why) > 50
        for t in (first, last):
            assert t is None or np.datetime64(t, "h")
