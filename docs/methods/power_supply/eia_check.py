"""Design 0014's check 3: the gas plant model against EIA-reported water at combined cycle plants on cooling towers, in aggregate only.

    WL_POWER_WORK=~/.cache/waterledger/power_water_work uv run python docs/methods/power_supply/eia_check.py

Input: EIA's thermoelectric cooling water data, 2024 detail file (EIA-923 Schedule 8D with EIA-860 cooling types), as
docs/methods/power_water/states.py reads it (its detail_all.pkl in $WL_POWER_WORK). Plants are combined cycle (generator primary technology
"Natural Gas Fired Combined Cycle") whose cooling is a recirculating tower (EIA-860 codes RI, RF, RN). Plant water is summed over unique
(plant, cooling system, month) rows and generation over unique (plant, generator, month), as states.py does. A plant-month is left out when
its consumption exceeds its withdrawal or 1,500 gal/MWh, or it reports no water with generation, the state table's screens.

Aggregates only (design 0014's scope rule): two regions, the Great Lakes states (IL, IN, MI, MN, NY, OH, PA, WI) and Texas, and a
region-month only with five plants or more. Each is generation-weighted water per MWh, gal/MWh. No plant is named or written out.

The model: gas.physics.hourly for a two-unit combined cycle on towers at central parameters, full output, at one ERA5 cell in each region
(West Michigan 42.75_-85.50 and central Texas 30.25_-97.75) over 2024 and over 1995-2024, monthly; and over 2024 again at the region's own fleet
heat rate (fuel over net generation in the same records, generation-weighted), since the model's heat rate is a new plant's and the fleet is
older. Nothing is tuned. Writes eia_check.csv next to this file and prints the comparison.
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd

from waterledger_data import era5
from waterledger_models import heat_rejection as hr
from waterledger_models.gas import physics as gp

HERE = Path(__file__).resolve().parent
WORK = Path(os.environ.get("WL_POWER_WORK", HERE.parent / "power_water" / "work")).expanduser()
W, C = "Water Withdrawal Volume (Million Gallons)", "Water Consumption Volume (Million Gallons)"
GEN = ["Net Generation from Steam Turbines (MWh)", "Net Generation Associated with Single Shaft Combined Cycle Units (MWh)",
       "Net Generation Associated with Combined Cycle Gas Turbines (MWh)"]
TOWERS = ("RI", "RF", "RN")
REGIONS = {"Great Lakes": ("IL", "IN", "MI", "MN", "NY", "OH", "PA", "WI"), "Texas": ("TX",)}
CELLS = {"Great Lakes": "42.75_-85.50", "Texas": "30.25_-97.75"}
MIN_PLANTS = 5
FUEL = "Fuel Consumption from All Fuel Types (MMBTU)"


def _towers():
    d = pd.read_pickle(WORK / "detail_all.pkl")
    d = d[d["Generator Primary Technology"].eq("Natural Gas Fired Combined Cycle")].copy()
    d["code"] = d["860 Cooling Type 1"].astype(str).str.extract(r"\((\w+)\)")[0]
    d = d[d.code.isin(TOWERS)]
    for c in [W, C, FUEL] + GEN:
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0.0)
    d["net"] = d[GEN].sum(axis=1)
    d["month"] = pd.to_numeric(d["Month"], errors="coerce").astype(int)
    return d


def fleet_heat_rate(d, states):
    """Btu/kWh (HHV): the region's fuel over its net generation, unique (plant, generator, month) rows with both."""
    g = d.drop_duplicates(["Plant Code", "Generator ID", "Month"])
    g = g[g.State.isin(states) & (g.net > 0) & (g[FUEL] > 0)]
    return g[FUEL].sum() * 1e6 / (g.net.sum() * 1000.0)


def eia(d):
    water = d.drop_duplicates(["Plant Code", "Cooling ID", "Month"]).groupby(["State", "Plant Code", "month"])[[W, C]].sum()
    gen = d.drop_duplicates(["Plant Code", "Generator ID", "Month"]).groupby(["State", "Plant Code", "month"])["net"].sum()
    pm = water.join(gen, how="inner").reset_index()
    pm = pm[(pm.net > 0)]
    gpm_c, gpm_w = pm[C] * 1e6 / pm.net, pm[W] * 1e6 / pm.net
    keep = (pm[W] > 0) & (pm[C] <= pm[W]) & (gpm_c <= 1500)
    pm = pm[keep]
    rows = []
    for region, states in REGIONS.items():
        r = pm[pm.State.isin(states)]
        for m, g in r.groupby("month"):
            n = g["Plant Code"].nunique()
            if n >= MIN_PLANTS:
                rows.append({"region": region, "month": m, "plants": n, "eia_consumed_gal_mwh": g[C].sum() * 1e6 / g.net.sum(),
                             "eia_withdrawn_gal_mwh": g[W].sum() * 1e6 / g.net.sum()})
    return pd.DataFrame(rows)


def model(cid, years=None, heat_rate=None):
    times, t, rh = era5.hourly(cid)
    times, t, rh = np.array(times), np.asarray(t, float), np.asarray(rh, float)
    if years:
        keep = np.isin(np.array([x[:4] for x in times]), [str(y) for y in years])
        times, t, rh = times[keep], t[keep], rh[keep]
    p = hr.for_location({**gp.central_parameters("cc", "towers"), **({"heat_rate": heat_rate} if heat_rate else {})}, t)
    h = gp.hourly(600.0, t, hr.wet_bulb(t, rh), rh, "cc", "towers", p, 2, 300.0)
    month = np.array([int(x[5:7]) for x in times])
    return {m: (h["consumed"][month == m].sum() / h["served"][month == m].sum(), h["withdrawn"][month == m].sum() / h["served"][month == m].sum())
            for m in range(1, 13)}


def main():
    d = _towers()
    e = eia(d)
    rates = {region: fleet_heat_rate(d, states) for region, states in REGIONS.items()}
    for region, cid in CELLS.items():
        for label, years, rate in (("2024", [2024], None), ("1995_2024", None, None), ("2024_fleet_hr", [2024], rates[region])):
            m = model(cid, years, rate)
            e.loc[e.region == region, f"model_{label}_consumed_gal_mwh"] = e.loc[e.region == region, "month"].map(lambda k: m[k][0])
            e.loc[e.region == region, f"model_{label}_withdrawn_gal_mwh"] = e.loc[e.region == region, "month"].map(lambda k: m[k][1])
    e = e.round(1)
    e.to_csv(HERE / "eia_check.csv", index=False)
    print(e.to_string(index=False))
    for region, g in e.groupby("region"):
        mean = lambda c: g[c].mean()
        summer, winter = g[g.month.isin([6, 7, 8])], g[g.month.isin([12, 1, 2])]
        swing = lambda c: summer[c].mean() / winter[c].mean()
        print(f"\n{region}: months {len(g)}, plants {g.plants.min()}-{g.plants.max()}, fleet heat rate {rates[region]:.0f} Btu/kWh")
        print(f"  consumed  EIA {mean('eia_consumed_gal_mwh'):.0f}  model 2024 {mean('model_2024_consumed_gal_mwh'):.0f} "
              f"(ratio {mean('model_2024_consumed_gal_mwh') / mean('eia_consumed_gal_mwh'):.2f}); summer/winter EIA {swing('eia_consumed_gal_mwh'):.2f}, "
              f"model {swing('model_2024_consumed_gal_mwh'):.2f}")
        print(f"  withdrawn EIA {mean('eia_withdrawn_gal_mwh'):.0f}  model 2024 {mean('model_2024_withdrawn_gal_mwh'):.0f} "
              f"(ratio {mean('model_2024_withdrawn_gal_mwh') / mean('eia_withdrawn_gal_mwh'):.2f})")
        print(f"  at the fleet heat rate: consumed {mean('model_2024_fleet_hr_consumed_gal_mwh'):.0f}, withdrawn "
              f"{mean('model_2024_fleet_hr_withdrawn_gal_mwh'):.0f}")


if __name__ == "__main__":
    main()
