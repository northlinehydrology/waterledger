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


def test_no_row_for_a_class_counted_in_two_bas():
    """Palo Verde is SRP's (EIA-930 counted it in AZPS too until Dec 4, 2019), St. Lucie FPL's, Colstrip NWMT's: the copies are out of
    the BAs' hours (grid930.DOUBLE_COUNTED), so AZPS nuclear, FMPP nuclear and PSEI coal have no row and no generation to carry one.
    SRP's nuclear is Palo Verde's own factor (cooling towers on reclaimed water, about 700 gal/MWh)."""
    t = pd.read_csv(en.BA_FUEL_TABLE)
    rows = set(map(tuple, t[["ba", "fuel"]].drop_duplicates().values))
    assert not {("AZPS", "nuclear"), ("FMPP", "nuclear"), ("PSEI", "coal")} & rows
    assert (en.ba_fuel_water("SRP")["nuclear"]["withdrawn"] < 1000).all()


def test_fallbacks_are_labeled():
    """A class with no EIA-923 generation in the BA says where its factor comes from [A]: the plants, the region or the U.S."""
    t = pd.read_csv(en.BA_FUEL_TABLE, keep_default_na=False)
    fb = t[t.basis.isin(["plant", "region"])]
    assert len(fb) and (fb.basis_from != "").all()
    assert (fb.groupby(["ba", "fuel"]).gen_mwh.sum() <= 0).all()        # no net EIA-923 generation in the BA that year
    assert set(t[t.basis == "plant"].basis_from) == {"2442", "2706"}


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
    bases = {r["basis"] for r in csv.DictReader(open(en.BA_FUEL_TABLE, encoding="utf-8"))}
    assert bases <= {"month", "year", "plant", "region", "us", "none", "missing"}
