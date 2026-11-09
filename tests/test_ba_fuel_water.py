"""Water by balancing authority, fuel class and month (design 0008, part 1, step 2): the table is complete where EIA-930
has a class, holds to the physics of each fuel, and gives back each BA's plant water."""
import csv

import numpy as np
import pytest

from waterledger_data import energy as en
from waterledger_data import grid930 as g


def test_every_fuel_every_month():
    f = en.ba_fuel_water("MISO")
    assert set(f) == set(g.FUELS)
    for fuel, d in f.items():
        for k, v in d.items():
            assert v.shape == (12,) and np.isfinite(v).all(), (fuel, k)


def test_no_water_classes_are_zero():
    f = en.ba_fuel_water("CISO")
    for fuel in ("hydro", "solar", "wind", "storage"):
        assert not f[fuel]["consumed"].any() and not f[fuel]["withdrawn"].any()


@pytest.mark.parametrize("ba", ["MISO", "PJM", "ERCO", "SWPP", "TVA", "SOCO"])
def test_consumed_within_withdrawn_and_plausible(ba):
    """Consumption can't exceed withdrawal, and no class's monthly consumption runs past what any cooling uses
    (Macknick et al. 2012: about 1,100 gal/MWh at most, for coal and nuclear towers)."""
    for fuel, d in en.ba_fuel_water(ba).items():
        assert (d["consumed"] <= d["withdrawn"] * 1.001 + 1e-9).all(), fuel
        assert (d["consumed"] <= 1500).all(), fuel
        assert (d["withdrawn_saline"] <= d["withdrawn"] + 1e-9).all(), fuel


def test_summer_above_winter_for_misos_steam():
    """Evaporation per MWh rises in warm months (Macknick; the plant reports agree)."""
    f = en.ba_fuel_water("MISO")
    for fuel in ("coal", "nuclear"):
        c = f[fuel]["consumed"]
        assert c[6:8].mean() > c[[0, 11]].mean(), fuel


def test_unknown_ba_has_none():
    assert en.ba_fuel_water("XXXX") is None


def test_basis_recorded():
    bases = {r["basis"] for r in csv.DictReader(open(en.BA_FUEL_TABLE))}
    assert bases <= {"month", "year", "us", "none", "missing"}
