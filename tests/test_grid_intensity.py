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
