"""Hourly power plant water by balancing authority (design 0008, part 1, step 3): a year of hours gives back the BA's
plant-reported water. Needs the EIA-930 cache (waterledger_data.grid930.build(), about 600 MB); set WATERLEDGER_FETCH=1
to build it, otherwise these are skipped. The nightly build fetches it."""
import os

import numpy as np
import pandas as pd
import pytest

from waterledger_data import energy as en
from waterledger_data import grid930 as g


@pytest.fixture(scope="module")
def cache():
    if not os.path.exists(os.path.join(g.RAW, "ba", "MISO.npz")):
        if not os.environ.get("WATERLEDGER_FETCH"):
            pytest.skip("set WATERLEDGER_FETCH=1 to build the EIA-930 cache")
        g.build()


def _plant_water():
    t = pd.read_csv(en.BA_FUEL_TABLE)
    t = t[t.ba != "US"]
    return t.assign(c=t.consumed_gal_mwh.fillna(0) * t.gen_mwh / 1e6,
                    w=t.withdrawn_gal_mwh.fillna(0) * t.gen_mwh / 1e6).groupby("ba")[["c", "w", "gen_mwh"]].sum()


# EIA-930 and EIA-923 count a BA's generation differently (plants on the border, pseudo-ties); the water follows the
# generation. Within 10% for the large organized markets and southeastern utilities; PSCO and BPAT are far apart
# (EIA-930 about 20% above EIA-923 for PSCO, 16% below for BPAT) and are left out.
@pytest.mark.parametrize("ba", ["MISO", "PJM", "ERCO", "SOCO", "NYIS", "ISNE", "FPL", "LGEE", "TVA", "DUK"])
def test_2024_gives_back_plant_water(cache, ba):
    x = g.intensity(ba)
    year = x["hour"].astype("datetime64[h]").astype("datetime64[Y]").astype(int) + 1970
    m = year == 2024
    gen = np.nan_to_num(x["generation"][m])
    got = np.nansum(x["consumed"][m] * gen) / 1e6
    assert got / _plant_water().c[ba] == pytest.approx(1.0, abs=0.10)


def test_each_hour_between_its_fuels(cache):
    """An hour's intensity is a generation-weighted mean of its fuels' factors, so it can't leave their range."""
    f = en.ba_fuel_water("MISO")
    x = g.intensity("MISO", f)
    month = x["hour"].astype("datetime64[h]").astype("datetime64[M]").astype(int) % 12
    lo = np.min([f[k]["consumed"][month] for k in g.FUELS], axis=0)
    hi = np.max([f[k]["consumed"][month] for k in g.FUELS], axis=0)
    c = x["consumed"]
    ok = ~np.isnan(c)
    # storage and pumped hydro can be negative, which lets the weights leave [0, 1]; allow for it
    assert (c[ok] >= lo[ok] - 1).mean() > 0.999 and (c[ok] <= hi[ok] + 1).mean() > 0.999


def test_consumed_within_withdrawn(cache):
    x = g.intensity("PJM")
    ok = ~np.isnan(x["consumed"])
    assert (x["consumed"][ok] <= x["withdrawn"][ok] + 1e-6).all()


# --- model 1.17: screened hours, fallback rows and a robust marginal slope ------------------------------------------------
import glob
import warnings

from waterledger_models import grid as G

BAS = sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(g.RAW, "ba", "*.npz")))


def _temp(hour):
    """A deterministic temperature for the bins (any series works for the range check: bins only split the hours)."""
    month, hod, _ = G.calendar(hour)
    return 10 + 12 * np.sin(2 * np.pi * (month - 3) / 12) + 5 * np.sin(2 * np.pi * (hod - 15) / 24) + \
        np.random.default_rng(0).normal(0, 3, len(hour))


def _table(ba):
    x = g.intensity(ba)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return x, G.fit(ba, x["hour"], x["consumed"], x["withdrawn"], x["generation"], _temp(x["hour"]), pair_ok=x["pair_ok"],
                        bounds=x["bounds"])


@pytest.mark.parametrize("ba", BAS)
def test_every_factor_within_the_bas_fuel_factors(cache, ba):
    """Every BA's average and marginal factors lie in the range of the fuel factors it generates with, in every month. A marginal
    slope can leave it a little at the edges (BPAT and AVRN slightly under 0 in summer, as hydro rises with load and gas falls;
    AECI in August 1.3 gal/MWh over its top factor): those are reported in meta["outside"], and none is over 2% of the range."""
    if en.ba_fuel_water(ba) is None:
        pytest.skip(f"{ba}: no plant water table (left out of the runs)")
    x, tab = _table(ba)
    if np.isfinite(x["consumed"]).sum() < 8760:
        pytest.skip(f"{ba}: under a year of hours (left out of the runs)")
    for kind, m, where, v, lo, hi in tab.meta["outside"]:
        assert kind.startswith("marginal_"), (kind, m, where, v, lo, hi)
        assert max(lo - v, v - hi) <= 0.02 * (hi - lo), (kind, m, where, v, lo, hi)


def test_azps_regression(cache):
    """AZPS before model 1.17: marginal 2,500-3,000 gal/MWh (single-hour spikes in "other" and nuclear read as 0 MW), "other" at
    1,600-5,700 (Solana's water over the BA's biomass) and nuclear at the U.S. 17,236 withdrawn (Palo Verde, filed under SRP). Palo Verde
    is SRP's alone: until Dec 4, 2019 EIA-930 counted it in both (tests/test_grid_double_count.py)."""
    h = lambda s: np.datetime64(s, "h")
    x, tab = _table("AZPS")
    hour = x["hour"].astype("datetime64[h]")
    for spike in ("2019-05-30T23", "2024-03-07T16", "2024-03-07T17", "2021-09-01T18", "2025-02-13T23"):
        i = np.searchsorted(hour, h(spike))
        assert np.isnan(x["consumed"][i]) and not x["pair_ok"][i] and not x["pair_ok"][i + 1], spike
    i = np.searchsorted(hour, h("2019-12-04T08"))           # Palo Verde, SRP's, is out of AZPS's hours on both sides (model 1.17)
    assert x["pair_ok"][i] and abs(x["generation"][i] - x["generation"][i - 1]) < 1000
    f = en.ba_fuel_water("AZPS")
    assert (f["nuclear"]["withdrawn"] < 1000).all() and (f["other"]["withdrawn"] < 100).all()
    assert (tab.marginal_withdrawn < 1200).all() and (tab.marginal_withdrawn > 150).all()
    assert (tab.withdrawn < 1200).all()
    gen = np.nan_to_num(x["generation"])
    assert np.nansum(x["withdrawn"] * gen) / gen[np.isfinite(x["withdrawn"])].sum() < 800


def test_every_reported_thermal_class_has_its_own_factor(cache):
    """A thermal class EIA-930 reports in a BA (over 0.1% of its generation) takes the U.S. factor only where neither a named plant
    nor its region has one (model 1.17)."""
    t = pd.read_csv(en.BA_FUEL_TABLE)
    rows = set(map(tuple, t[["ba", "fuel"]].drop_duplicates().values))
    us_ok = {("NYIS", "coal")}                                   # New York's region is NYIS alone, with no coal since 2020
    for ba in sorted(set(t.ba) - {"US"}):
        try:
            d = g.hourly(ba)
        except FileNotFoundError:
            continue
        pos = {k: float(np.nansum(np.clip(d[k], 0, None))) for k in g.FUELS}
        for fuel in ("coal", "gas", "nuclear", "oil", "other"):
            if pos[fuel] > 0.001 * sum(pos.values()):
                assert (ba, fuel) in rows, (ba, fuel)
                basis = set(t[(t.ba == ba) & (t.fuel == fuel)].basis)
                assert "us" not in basis or (ba, fuel) in us_ok, (ba, fuel, basis)
