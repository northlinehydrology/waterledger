"""The cooling run worked a block of hours at a time (cooling.HOUR_BLOCK, model 1.8) gives the same numbers, to the bit, as the whole
record at once: every step of the heat balance is the same calculation on each hour, and the statistics are taken over the same whole
series in the same order."""
import numpy as np

import golden
from waterledger_models.datacenter import cooling as cw
from waterledger_models.datacenter.physics import for_location, peak_utilization, wet_bulb


def test_a_run_by_blocks_is_the_whole_record_to_the_bit():
    times, t, rh = golden.weather()
    whole = cw.run_location(times, t, rh, n=8, block=None)
    assert cw.run_location(times, t, rh, n=8) == whole                       # HOUR_BLOCK, the default
    assert cw.run_location(times, t, rh, n=8, block=1000) == whole           # blocks that don't divide the record, and a short last block


def test_every_hourly_series_by_blocks_is_the_whole_record_to_the_bit():
    times, t, rh = golden.weather()
    tdb, rh = np.asarray(t, float), np.asarray(rh, float)
    twb = wet_bulb(tdb, rh)
    for design in cw.DESIGNS:
        for p in cw.sample(3, 7) + [cw.central()]:
            p = for_location(p, tdb)
            at_peak = {**p, "utilization": float(peak_utilization(p))}
            got = cw._hourly_run(tdb, twb, rh, design, p, at_peak, 777)
            want = cw._hourly_run(tdb, twb, rh, design, p, at_peak, None)
            assert all(np.array_equal(a, b) for a, b in zip(got, want)), design


def test_daily_stats_by_groups_are_the_masked_statistics_to_the_bit():
    times, t, rh = golden.weather()
    days = np.array([x[:10] for x in times])
    uniq, idx = np.unique(days, return_inverse=True)
    years, months = np.array([d[:4] for d in uniq]), np.array([d[:7] for d in uniq])
    g = np.random.default_rng(1).gamma(2.0, 0.1, len(times))
    assert cw.daily_stats(idx, len(uniq), years, g, 850.0, months, by=(cw.groups(years), cw.groups(months))) == cw.daily_stats(idx, len(uniq), years, g, 850.0, months)
    assert [s.stop - s.start for s in cw.groups(years)] == [365, 366]
