"""No plant's generation in two balancing authorities' hours (model 1.17): EIA-930 counted Palo Verde in AZPS and SRP until Dec 4,
2019, St. Lucie's municipal shares in FMPP as well as FPL, and Puget Sound Energy's Colstrip share in PSEI as well as NWMT
(grid930.DOUBLE_COUNTED). Needs the EIA-930 cache (waterledger_data.grid930.build()); set WATERLEDGER_FETCH=1 to build it,
otherwise these are skipped."""
import os

import numpy as np
import pytest

from waterledger_data import grid930 as g


@pytest.fixture(scope="module")
def cache():
    if not os.path.exists(os.path.join(g.RAW, "ba", "MISO.npz")):
        if not os.environ.get("WATERLEDGER_FETCH"):
            pytest.skip("set WATERLEDGER_FETCH=1 to build the EIA-930 cache")
        g.build()
    bas = sorted(f[:-4] for f in os.listdir(os.path.join(g.RAW, "ba")) if f.endswith(".npz") and not f.endswith(".part.npz"))
    return {ba: g.hourly(ba) for ba in bas}


def _on(d, h0, n, cls):
    a = np.full(n, np.nan)
    a[d["hour"] - h0] = d[cls]
    return a


def test_no_class_copied_hour_for_hour_into_another_ba(cache):
    """A copied series is equal within 0.5% and steps by the same MW in the same hour. By chance two fleets of similar size do that
    in at most 0.15% of their shared hours (ISNE and NYIS nuclear, about 3.3 GW each); AZPS's copy of Palo Verde did in 13%."""
    h0 = min(d["hour"].min() for d in cache.values())
    n = max(d["hour"].max() for d in cache.values()) - h0 + 1
    for cls in g.FUELS:
        s = {ba: _on(d, h0, n, cls) for ba, d in cache.items()}
        s = {ba: a for ba, a in s.items() if np.nansum(np.abs(a)) > 0}
        keys = sorted(s)
        for i, a in enumerate(keys):
            for b in keys[i + 1:]:
                x, y = s[a], s[b]
                both = (x > 50) & (y > 50)
                if both.sum() < 24:
                    continue
                dx, dy = np.diff(x, prepend=np.nan), np.diff(y, prepend=np.nan)
                same = both & (np.abs(x - y) <= 0.005 * np.maximum(x, y)) & (np.abs(dx) > 5) & (np.abs(dx - dy) <= 1)
                assert same.sum() <= 0.01 * both.sum(), (cls, a, b, int(same.sum()), int(both.sum()))


# EIA-923's lower-48 nuclear net generation by year, TWh (Schedules 2-5, final revisions 2019-2023 and final 2024;
# https://www.eia.gov/electricity/data/eia923/), against the sum over BAs of EIA-930's nuclear (hour starting in the year, UTC)
EIA923_NUCLEAR = {2019: 809.409, 2020: 789.879, 2021: 779.645, 2022: 771.537, 2023: 774.873, 2024: 781.865}


def test_the_bas_nuclear_adds_up_to_the_countrys(cache):
    """Nuclear plants run near full output and EIA-930 has no small plants to miss, so the BAs' sum is EIA-923's within 1% every year
    (2019 was 3.8% over with Palo Verde in AZPS and SRP)."""
    tot = dict.fromkeys(EIA923_NUCLEAR, 0.0)
    for d in cache.values():
        year = (d["hour"] - 1).astype("datetime64[h]").astype("datetime64[Y]").astype(int) + 1970
        for y in tot:
            tot[y] += float(np.nansum(d["nuclear"][year == y])) / 1e6
    for y, v in tot.items():
        assert abs(v / EIA923_NUCLEAR[y] - 1) < 0.01, (y, v)


def test_each_double_count_is_out_of_the_copy_and_in_the_whole_plants_ba(cache):
    for ba, cls, first, last, holder, _ in g.DOUBLE_COUNTED:
        twice = g.double_counted(ba, cache[ba]["hour"])[cls]
        raw = g.hourly(ba, raw=True)[cls]
        assert np.nansum(np.clip(raw[twice], 0, None)) > 0, (ba, cls)                 # EIA-930 does count it there
        assert np.isnan(cache[ba][cls][twice]).all(), (ba, cls)
        h = cache[holder]
        at = np.isin(h["hour"], cache[ba]["hour"][twice & (np.nan_to_num(raw) > 0)])
        assert np.nanmean(h[cls][at]) > np.nanmean(raw[np.isin(cache[ba]["hour"], h["hour"][at])]), (holder, cls)


def test_azps_regression(cache):
    """AZPS's 2019 hours carried Palo Verde's whole 4 GW as SRP's did: 29.2 TWh of the 50.3 TWh EIA-930 put in AZPS in 2019. Now AZPS
    has no nuclear in any hour (0 MW or not reported); SRP keeps the plant."""
    a, s = cache["AZPS"], cache["SRP"]
    assert np.nansum(np.abs(a["nuclear"])) == 0
    y19 = lambda d: (d["hour"] - 1).astype("datetime64[h]").astype("datetime64[Y]").astype(int) == 49
    assert 29.0 < np.nansum(g.hourly("AZPS", raw=True)["nuclear"][y19(a)]) / 1e6 < 29.5
    assert 31.0 < np.nansum(s["nuclear"][y19(s)]) / 1e6 < 33.0
    gen = np.nansum(np.vstack([a[k] for k in g.FUELS]), axis=0)
    assert 20.5 < np.nansum(gen[y19(a)]) / 1e6 < 21.5 and np.nanmax(gen[y19(a)]) < 9000      # with Palo Verde: 50.3 TWh, peak 12.2 GW
