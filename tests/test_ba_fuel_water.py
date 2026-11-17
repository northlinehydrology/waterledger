"""Water by balancing authority, fuel class and month (design 0008, part 1, step 2): the table is complete where EIA-930
has a class, holds to the physics of each fuel, and gives back each BA's plant water."""
import csv

import numpy as np
import pandas as pd
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
    """Hydro, wind and storage carry no water anywhere; solar only where the BA has a concentrating solar plant reporting cooling
    water (model 1.17: AZPS's Solana, CISO's Mojave, NEVP's Crescent Dunes), whose water is in the class EIA-930 counts its output in."""
    t = pd.read_csv(en.BA_FUEL_TABLE)
    t = t[t.ba != "US"]
    for fuel in ("hydro", "wind", "storage"):
        x = t[t.fuel == fuel]
        assert (x.consumed_gal_mwh == 0).all() and (x.withdrawn_gal_mwh == 0).all(), fuel
    wet = set(t[(t.fuel == "solar") & (t.withdrawn_gal_mwh > 0)].ba)
    assert wet == {"AZPS", "CISO", "NEVP"}
    assert (t[t.fuel == "solar"].consumed_gal_mwh <= 400).all()


def test_csp_water_is_not_in_other():
    """Before model 1.17 Solana's water fell to "other" and was divided by AZPS's biomass and landfill gas: 1,600-5,700 gal/MWh."""
    for ba in ("AZPS", "CISO", "NEVP"):
        assert (en.ba_fuel_water(ba)["other"]["withdrawn"] < 100).all(), ba


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
