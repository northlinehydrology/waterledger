"""Design 0019's check F1: gas fuel cell plants' heat rate as EIA reports it, in aggregate only, against gas.physics' fuel cell range and its age
bands.

    WL_POWER_WORK=~/.cache/waterledger/power_water_work uv run python docs/methods/power_supply/fuel_cell_check.py

Input: EIA-860 2024 (3_1_Generator: prime mover FC, energy source NG; the plant's nameplate and the year its first and last fuel cells came
online) and EIA-923 2022, 2023 and 2024 (Page 1: prime mover FC, fuel NG, electric fuel in MMBtu and net generation), as the other checks keep
them under $WL_POWER_WORK. A plant's heat rate is its electric fuel (HHV) over its net generation. Groups: all plants with 2024 generation; those not
CHP over 50% capacity factor (CHP plants' fuel includes useful heat); those of 1-5 MW (EIA names no manufacturer; the size most like solid oxide
servers, the larger plants including molten carbonate units [A]); and, of the 1-5 MW plants over 50% in each of 2022-2024, by the year they came
online, each year. Groups of five plants or more only (design 0014's scope rule); no plant is named or written. Writes fuel_cell_check.csv next to
this file and prints it.
"""
import os
from pathlib import Path

import pandas as pd

from waterledger_models.gas import physics as gp

HERE = Path(__file__).resolve().parent
WORK = Path(os.environ.get("WL_POWER_WORK", "~/.cache/waterledger/power_water_work")).expanduser()
F923 = {2022: WORK / "dl2022" / "x923" / "EIA923_Schedules_2_3_4_5_M_12_2022_Final_Revision.xlsx",
        2023: WORK / "dl2023" / "x923" / "EIA923_Schedules_2_3_4_5_M_12_2023_Final_Revision.xlsx",
        2024: WORK / "dl" / "f923" / "EIA923_Schedules_2_3_4_5_M_12_2024_Final.xlsx"}
MIN_PLANTS = 5
COHORTS = {"online 2021": (2021, 2021), "online 2020": (2020, 2020), "online 2019": (2019, 2019), "online 2018": (2018, 2018),
           "online 2016-2017": (2016, 2017), "online by 2015": (0, 2015)}


def plants():
    g = pd.read_excel(WORK / "dl" / "eia860" / "x" / "3_1_Generator_Y2024.xlsx", "Operable", header=1)
    g = g[g["Prime Mover"].eq("FC") & g["Energy Source 1"].eq("NG")].copy()
    g["mw"] = pd.to_numeric(g["Nameplate Capacity (MW)"], errors="coerce")
    g["yr"] = pd.to_numeric(g["Operating Year"], errors="coerce")
    return g.groupby("Plant Code").agg(mw=("mw", "sum"), first=("yr", "min"))


def year(y):
    f = pd.read_excel(F923[y], "Page 1 Generation and Fuel Data", header=5)
    f = f[f["Reported\nPrime Mover"].eq("FC") & f["Reported\nFuel Type Code"].eq("NG")]
    by = f["Plant Id"]
    return pd.DataFrame({"fuel": pd.to_numeric(f["Elec Fuel Consumption\nMMBtu"], errors="coerce").groupby(by).sum(),
                         "gen": pd.to_numeric(f["Net Generation\n(Megawatthours)"], errors="coerce").groupby(by).sum(),
                         "chp": f["Combined Heat And\nPower Plant"].astype(str).str.strip().eq("Y").groupby(by).any()})


def row(name, d, y, hours):
    if len(d) < MIN_PLANTS:
        return None
    hr = d[f"fuel_{y}"] * 1e3 / d[f"gen_{y}"]
    return {"group": name, "year": y, "plants": len(d), "mw": round(d.mw.sum(), 1), "fleet_heat_rate": round(d[f"fuel_{y}"].sum() * 1e3 / d[f"gen_{y}"].sum()),
            "plant_p25": round(hr.quantile(0.25)), "plant_median": round(hr.median()), "plant_p75": round(hr.quantile(0.75)),
            "capacity_factor": round(d[f"gen_{y}"].sum() / (d.mw.sum() * hours), 3)}


def main():
    d = plants()
    for y in F923:
        d = d.join(year(y).add_suffix(f"_{y}"), how="left")
    hours = {2022: 8760, 2023: 8760, 2024: 8784}
    rows = []
    has = d[(d.gen_2024 > 0) & (d.fuel_2024 > 0)]
    rows.append(row("all with 2024 generation", has, 2024, 8784))
    steady = has[~has.chp_2024.fillna(False).astype(bool) & (has.gen_2024 > 0.5 * has.mw * 8784)]
    steady = steady[(steady.fuel_2024 * 1e3 / steady.gen_2024).between(4000, 15000)]
    rows.append(row("not CHP, over 50% capacity factor", steady, 2024, 8784))
    rows.append(row("the same, 1-5 MW", steady[(steady.mw >= 1) & (steady.mw < 5)], 2024, 8784))
    rows.append(row("the same, 5 MW and over", steady[steady.mw >= 5], 2024, 8784))
    three = d[(d.mw >= 1) & (d.mw < 5)].copy()
    for y in F923:
        three = three[~three[f"chp_{y}"].fillna(False).astype(bool) & (three[f"gen_{y}"] > 0.5 * three.mw * hours[y])]
        three = three[(three[f"fuel_{y}"] * 1e3 / three[f"gen_{y}"]).between(4000, 15000)]
    for y in F923:
        rows.append(row("1-5 MW, not CHP, over 50% in each of 2022-2024", three, y, hours[y]))
    for name, (a, b) in COHORTS.items():
        c = three[three["first"].between(a, b)]
        for y in F923:
            rows.append(row(f"1-5 MW steady, {name}", c, y, hours[y]))
    out = pd.DataFrame([r for r in rows if r])
    out.to_csv(HERE / "fuel_cell_check.csv", index=False)
    print(out.to_string(index=False))
    lo, hi = gp.TECH["fuel_cell"]["heat_rate"]
    print(f"\ngas.physics fuel cell heat rate {lo:.0f}-{hi:.0f}; age bands {[(a, b, r) for a, b, r in gp.AGE_HEAT_RATE]}")
    ch = (three.fuel_2024 / three.gen_2024) / (three.fuel_2022 / three.gen_2022) - 1
    print(f"a plant's own change 2022 to 2024: median {ch.median():+.3f}, p10-p90 {ch.quantile(0.1):+.3f} to {ch.quantile(0.9):+.3f}")


if __name__ == "__main__":
    main()
