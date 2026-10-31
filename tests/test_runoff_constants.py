"""Constants the site reads and the single-storm method."""
from waterledger_models import hydrology, runoff


def test_rain_median():
    assert runoff.rain_median({"a": 30.0, "b": 34.0, "c": 40.0}) == 34.0
    assert runoff.rain_median({"a": 30.0, "b": 34.0}) == 32.0


def test_storm_by_curve_number_not_in_proportion():
    one = runoff.storm_mg(200, 1.0, 0.5)
    assert abs(one - 0.5 * hydrology.scs_runoff_in(1.0, 98) * 200 * 27154 / 1e6) < 1e-9      # lawn sheds nothing from an inch at CN 65
    assert runoff.storm_mg(200, 2.57, 0.5) > 2.57 * one                                      # runoff rises faster than the rain


def test_salt_takes_a_region_events():
    base = runoff.salt(100, 0.5)["salt_t"][1]
    assert runoff.salt(100, 0.5, events=[10, 80, 120])["salt_t"][1] == 2 * base
