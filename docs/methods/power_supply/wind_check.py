"""Design 0014's check 5 for wind: the wind chain on ERA5's 100 m wind (supply/wind.py) against EIA's reported output at onshore wind plants,
in aggregate only.

    WL_POWER_WORK=~/.cache/waterledger/power_water_work uv run python docs/methods/power_supply/wind_check.py

Input: EIA-860 2024 (3_1_Generator: every generator at a plant; 3_2_Wind: hub height; 2___Plant: latitude and longitude) and EIA-923 2024
(Page 1, net generation), unzipped under $WL_POWER_WORK/dl/eia860/x and $WL_POWER_WORK/dl/f923. A plant is in the check when every one of its
operable generators is onshore wind (prime mover WT) and operating (status OP), each online before January 2024, with no generator of any kind
retired in 2024 or after, its nameplate summed over the generators at least 5 MW, in the lower 48 states, and its 2024 net generation for prime
mover WT in EIA-923 above zero.

Observed: a state's fleet capacity factor, the plants' summed 2024 net generation over their summed nameplate x 8,784 hours. Modeled: the wind
chain on the plant's ERA5 cell (era5.cell's land rule, as est.supply uses it) for the hours of 2024 in local standard time, at wind.RANGES'
midpoints with resource 1.0, capacity-weighted the same way, two ways:

  at 110 m      wind.hourly as it is, the IEA 3.4 MW reference turbine at its 110 m hub (what est.supply runs for a new project)
  at own hub    the same chain at the plant's hub height: 100 m speed x resource x (hub / 100)^alpha through wind.power_curve, less losses.
                wind.hourly fixes the hub at wind.HUB_M, so this composes wind.power_curve directly; nothing in the package changes. The hub is
                EIA-860's capacity-weighted over the plant's generators, else wind.HUB_M.

Also: the resource factor that makes the modeled fleet equal the observed one for each (the chain run on a grid of factors, interpolated);
the fleet without plants whose own ratio is outside TRIM; the interior (Great Lakes states, Central Plains, Texas); cohorts by online year, all
plants and the interior's (hub heights and rotors grew); plants by their cell's mean 2024 100 m speed (ERA5's 0.25 degree grid smooths ridge
and pass sites into slow cells); and by month for five regions, from monthly respondents only (EIA-923 imputes annual respondents' months).
EIA-860 gives no rotor diameter, so the turbines' specific power is not separated from the rest. Nothing is tuned.

Aggregates only (design 0014's scope rule): a state is written only with five plants or more. No plant is named or written out. The 2024 100 m
wind at the cells is fetched from ERA5's open copy (era5.OPEN_COPY) into $WL_POWER_WORK/wind_check_era5_2024, apart from the raw cache since it
is one year only; cells pv_check.py already fetched are read from its cache. Writes wind_check.csv and wind_check_monthly.csv next to this file
and prints the tables.
"""
import os, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from waterledger_data import era5
from waterledger_models.supply import wind

HERE = Path(__file__).resolve().parent
WORK = Path(os.environ.get("WL_POWER_WORK", "~/.cache/waterledger/power_water_work")).expanduser()
E860, E923 = WORK / "dl" / "eia860" / "x", WORK / "dl" / "f923"
WX, WX_PV = WORK / "wind_check_era5_2024", WORK / "pv_check_era5_2024"
NOT_L48 = ("AK", "HI", "PR", "GU", "VI", "AS", "MP")
MIN_PLANTS, MIN_MW = 5, 5.0
HOURS = 8784                                     # 2024
YEAR = 2024
VARS = ("wind_u_component_100m", "wind_v_component_100m")
U0 = np.datetime64(f"{YEAR - 1}-12-31T00", "h")  # UTC, wide enough for local standard time in 2024 anywhere in the states
U1 = np.datetime64(f"{YEAR + 1}-01-01T12", "h")
FACTORS = np.round(np.arange(0.70, 1.401, 0.01), 2)
TRIM = (0.5, 1.5)                                # observed over modeled outside this: a plant out for months, repowered or misreported [A]
GREAT_LAKES = ("MI", "OH", "IN", "WI", "MN", "IL", "PA", "NY")
REGIONS = {"Great Lakes states": GREAT_LAKES, "Central Plains (IA, MO, KS, NE, SD, ND, OK)": ("IA", "MO", "KS", "NE", "SD", "ND", "OK"),
           "Texas": ("TX",), "West (MT, WY, CO, NM, ID, UT, AZ, NV, CA, OR, WA)": ("MT", "WY", "CO", "NM", "ID", "UT", "AZ", "NV", "CA", "OR", "WA"),
           "Northeast and South (rest)": None}
INTERIOR = GREAT_LAKES + REGIONS["Central Plains (IA, MO, KS, NE, SD, ND, OK)"] + ("TX",)
INTERIOR_NAME = "Interior (Great Lakes states, Central Plains, Texas)"
SPEED_BINS = ((0, 5.5), (5.5, 6.5), (6.5, 7.0), (7.0, 99))
COHORTS = {"online before 2010": (0, 2009), "online 2010-2018": (2010, 2018), "online 2019-2023": (2019, 2023)}
MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")
CENTRAL = {k: (a + b) / 2 for k, (a, b) in wind.RANGES.items()}
FT = 0.3048


def plants():
    """The check's plants: code, state, lat, lon, mw, hub_m, hub_own, year. In memory only."""
    x = pd.ExcelFile(E860 / "3_1_Generator_Y2024.xlsx")
    g = pd.read_excel(x, "Operable", header=1)
    r = pd.read_excel(x, "Retired and Canceled", header=1)
    g["mw"] = pd.to_numeric(g["Nameplate Capacity (MW)"], errors="coerce")
    g["year"] = pd.to_numeric(g["Operating Year"], errors="coerce")
    g["wt"] = g["Prime Mover"].eq("WT")
    g["op"] = g.Status.eq("OP")
    g["new"] = g.year.fillna(9999) >= YEAR
    retired = set(r.loc[pd.to_numeric(r["Retirement Year"], errors="coerce") >= YEAR, "Plant Code"])
    p = g.groupby("Plant Code").agg(state=("State", "first"), wt=("wt", "all"), op=("op", "all"), new=("new", "any"), mw=("mw", "sum"))
    p = p[p.wt & p.op & ~p.new & ~p.index.isin(retired) & (p.mw >= MIN_MW) & ~p.state.isin(NOT_L48)]
    w = pd.read_excel(E860 / "3_2_Wind_Y2024.xlsx", "Operable", header=1)
    w = w[w["Plant Code"].isin(p.index)].copy()
    w["mw"] = pd.to_numeric(w["Nameplate Capacity (MW)"], errors="coerce")
    w["hub"] = pd.to_numeric(w["Turbine Hub Height (Feet)"], errors="coerce") * FT
    w["year"] = pd.to_numeric(w["Operating Year"], errors="coerce")
    w["hw"] = w.hub * w.mw
    w["yw"] = w.year * w.mw
    w["mw_hub"] = w.mw.where(w.hub.notna(), 0.0)
    a = w.groupby("Plant Code").agg(hw=("hw", "sum"), mw_hub=("mw_hub", "sum"), yw=("yw", "sum"), mw_w=("mw", "sum"))
    p = p.join(a)
    p["hub_own"] = p.mw_hub.fillna(0) >= 0.999 * p.mw
    p["hub_m"] = np.where(p.mw_hub.fillna(0) > 0, p.hw / p.mw_hub, wind.HUB_M)
    p["year"] = np.where(p.mw_w.fillna(0) > 0, p.yw / p.mw_w, np.nan)
    pl = pd.read_excel(E860 / "2___Plant_Y2024.xlsx", header=1).set_index("Plant Code")
    p = p.join(pl[["Latitude", "Longitude"]].rename(columns={"Latitude": "lat", "Longitude": "lon"}))
    return p.dropna(subset=["lat", "lon"])[["state", "lat", "lon", "mw", "hub_m", "hub_own", "year"]]


def generation():
    """2024 net generation, MWh, by plant, prime mover WT (EIA-923 Page 1): the year ("gen"), each month (1-12), and whether it reports monthly."""
    f = pd.read_excel(E923 / "EIA923_Schedules_2_3_4_5_M_12_2024_Final.xlsx", "Page 1 Generation and Fuel Data", header=5)
    f = f[f["Reported\nPrime Mover"].eq("WT")]
    cols = {"Net Generation\n(Megawatthours)": "gen", **{f"Netgen\n{m}": i + 1 for i, m in enumerate(MONTHS)}}
    out = f[list(cols)].apply(pd.to_numeric, errors="coerce").groupby(f["Plant Id"]).sum().rename(columns=cols)
    out["monthly"] = f["Respondent\nFrequency"].astype(str).str.strip().eq("M").groupby(f["Plant Id"]).all()
    return out


def _read(job):
    import fsspec, omfiles
    var, key, t0, groups = job
    r = omfiles.OmFileReader.from_fsspec(fsspec.filesystem("s3", anon=True), f"{era5.OPEN_COPY}/{var}/chunk_{key}.om")
    out = {}
    for (i, b), cells in groups:
        row = np.asarray(r[i + 360, 6 * b:6 * b + 6, :], dtype=np.float32)       # the file's chunks are 1 x 6 cells x 504 hours
        for c in cells:
            out[c] = row[era5.indexes(c)[1] + 720 - 6 * b]
    return var, t0, out


def weather(cells, workers=48):
    """{cell: (month in local standard time, 100 m speed)} for the hours of 2024, fetched once into WX (or read from pv_check.py's cache)."""
    WX.mkdir(parents=True, exist_ok=True)
    todo = sorted(c for c in set(cells) if not (WX / f"{c}.npz").exists() and not (WX_PV / f"{c}.npz").exists())
    if todo:
        h0, h1 = int(U0.astype(np.int64)), int(U1.astype(np.int64))
        keys = range(h0 // 504, (h1 - 1) // 504 + 1)
        by = {}
        for c in todo:
            i, j = era5.indexes(c)
            by.setdefault((i, (j + 720) // 6), []).append(c)
        groups = sorted(by.items())
        batches = [groups[k:k + 40] for k in range(0, len(groups), 40)]
        jobs = [(v, k, k * 504, b) for v in VARS for k in keys for b in batches]
        print(f"fetching 2024 100 m wind for {len(todo)} cells: {len(jobs)} reads of up to 40 cell groups")
        with ThreadPoolExecutor(workers) as pool:
            got = list(pool.map(_read, jobs))
        for c in todo:
            series = {}
            for v in VARS:
                x = np.full(h1 - h0, np.nan, dtype=np.float32)
                for var, t0, vals in got:
                    if var == v and c in vals:
                        lo, hi = max(t0, h0), min(t0 + 504, h1)
                        x[lo - h0:hi - h0] = vals[c][lo - t0:hi - t0]
                series[v] = x
            np.savez_compressed(WX / f"{c}.npz", start_utc=str(U0), **series)
    out = {}
    for c in set(cells):
        z = np.load(WX / f"{c}.npz" if (WX / f"{c}.npz").exists() else WX_PV / f"{c}.npz")
        utc = np.datetime64(str(z["start_utc"]), "h") + np.arange(len(z[VARS[0]]))
        lst = utc + np.timedelta64(round(era5.indexes(c)[1] / 4 / 15), "h")
        keep = lst.astype("datetime64[Y]").astype(int) + 1970 == YEAR
        u, v = (z[k].astype(float)[keep] for k in VARS)
        if keep.sum() != HOURS or np.isnan(u).any() or np.isnan(v).any():
            raise ValueError(f"ERA5 cell {c}: 2024 hours missing")
        out[c] = (lst[keep].astype("datetime64[M]").astype(int) % 12 + 1, np.hypot(u, v))
    return out


def chain(s100, hub, p):
    """Output per MW of nameplate each hour at hub height `hub`, m: wind.hourly's chain with the hub as an input."""
    return wind.power_curve(s100 * p["resource"] * (hub / 100.0) ** p["alpha"]) * (1.0 - p["losses"])


def model(pl, wx):
    """Each plant's modeled 2024 capacity factor at 110 m and at its own hub, at central RANGES and at each of FACTORS, and by month (own hub)."""
    rows, g110, ghub, monthly = [], [], [], []
    for code, row in pl.iterrows():
        month, s = wx[row.cell]
        h = chain(s, row.hub_m, CENTRAL)
        rows.append((float(chain(s, wind.HUB_M, CENTRAL).mean()), float(h.mean())))
        monthly.append([float(h[month == m].sum()) * row.mw for m in range(1, 13)])         # MWh
        g110.append([float(chain(s, wind.HUB_M, {**CENTRAL, "resource": f}).mean()) for f in FACTORS])
        ghub.append([float(chain(s, row.hub_m, {**CENTRAL, "resource": f}).mean()) for f in FACTORS])
    pl = pl.assign(cf_110=[a for a, _ in rows], cf_hub=[b for _, b in rows], speed_100=[float(wx[c][1].mean()) for c in pl.cell])
    return (pl, pd.DataFrame(g110, index=pl.index, columns=FACTORS), pd.DataFrame(ghub, index=pl.index, columns=FACTORS),
            pd.DataFrame(monthly, index=pl.index, columns=range(1, 13)))


def _match(g, grid, obs):
    w = g.mw / g.mw.sum()
    curve = (grid.loc[g.index].mul(w, axis=0)).sum().values                # fleet CF at each factor; rises with the factor
    return float(np.interp(obs, curve, FACTORS)) if curve[0] <= obs <= curve[-1] else np.nan


def _row(name, g, g110, ghub):
    w = g.mw / g.mw.sum()
    obs = g.gen.sum() / (g.mw.sum() * HOURS)
    m110, mhub = float((g.cf_110 * w).sum()), float((g.cf_hub * w).sum())
    r = g.gen / (g.mw * HOURS) / g.cf_hub
    tr = g[r.between(*TRIM)]
    return {"group": name, "plants": len(g), "mw": round(g.mw.sum()), "hub_m_mean": round(float((g.hub_m * w).sum()), 1),
            "hub_own_share": round(float(g.hub_own.mean()), 2), "online_year_mean": round(float((g.year * w).sum()), 1),
            "era5_100m_speed_mean": round(float((g.speed_100 * w).sum()), 2), "cf_observed": round(obs, 4),
            "cf_model_110m": round(m110, 4), "ratio_110m": round(obs / m110, 3), "resource_match_110m": round(_match(g, g110, obs), 3),
            "cf_model_own_hub": round(mhub, 4), "ratio_own_hub": round(obs / mhub, 3), "resource_match_own_hub": round(_match(g, ghub, obs), 3),
            "plants_trimmed_out": int(len(g) - len(tr)),
            "ratio_own_hub_trimmed": round((tr.gen.sum() / (tr.mw.sum() * HOURS)) / float((tr.cf_hub * tr.mw).sum() / tr.mw.sum()), 3),
            "plant_ratio_own_hub_p25_p50_p75": "/".join(f"{x:.2f}" for x in r.quantile([0.25, 0.5, 0.75]))}


def main():
    t0 = time.time()
    pl = plants()
    gen = generation()
    n0 = len(pl)
    pl = pl.join(gen, how="inner")
    pl = pl[pl.gen > 0]
    print(f"plants: {n0} by EIA-860, {len(pl)} with 2024 WT net generation in EIA-923; {pl.hub_own.mean():.0%} with EIA's hub height for all their MW")
    pl["cell"] = [era5.cell(a, b)["id"] for a, b in zip(pl.lat, pl.lon)]
    wx = weather(pl.cell)
    print(f"weather ready at {time.time() - t0:.0f} s ({pl.cell.nunique()} cells)")
    pl, g110, ghub, mon = model(pl, wx)
    rows = [_row(s, g, g110, ghub) for s, g in pl.groupby("state") if len(g) >= MIN_PLANTS]
    for name, states in REGIONS.items():
        g = pl[pl.state.isin(states)] if states else pl[~pl.state.isin([s for v in REGIONS.values() if v for s in v])]
        if len(g) >= MIN_PLANTS:
            rows.append(_row(name, g, g110, ghub))
    interior = pl[pl.state.isin(INTERIOR)]
    rows.append(_row(INTERIOR_NAME, interior, g110, ghub))
    for name, (a, b) in COHORTS.items():
        rows.append(_row(name, pl[pl.year.round().between(a, b)], g110, ghub))
        rows.append(_row(f"{INTERIOR_NAME}, {name}", interior[interior.year.round().between(a, b)], g110, ghub))
    for a, b in SPEED_BINS:
        rows.append(_row(f"ERA5 100 m mean speed {a}-{b} m/s", pl[pl.speed_100.between(a, b, inclusive="left")], g110, ghub))
    rows.append(_row("All plants in the check", pl, g110, ghub))
    out = pd.DataFrame(rows)
    out.to_csv(HERE / "wind_check.csv", index=False)
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(out.to_string(index=False))
    st = out[out.group.str.len() == 2]
    for col in ("ratio_110m", "ratio_own_hub"):
        w = st.mw / st.mw.sum()
        print(f"\nstate {col}: capacity-weighted mean {float((st[col] * w).sum()):.3f}, median {st[col].median():.3f}, "
              f"range {st[col].min():.3f}-{st[col].max():.3f}")
    ten = out[(out.group.str.len() == 2) & (out.plants >= 10)]
    for col in ("resource_match_110m", "resource_match_own_hub"):
        print(f"{col}, states with 10+ plants ({len(ten)}): {ten[col].min():.3f}-{ten[col].max():.3f}, "
              f"p10-p90 {ten[col].quantile(0.1):.3f}-{ten[col].quantile(0.9):.3f}, median {ten[col].median():.3f}")
    tin = ten[ten.group.isin(INTERIOR)]
    for col in ("resource_match_110m", "resource_match_own_hub"):
        print(f"{col}, interior states with 10+ plants ({len(tin)}): {tin[col].min():.3f}-{tin[col].max():.3f}, median {tin[col].median():.3f}")
    print(f"ratio (own hub) against modeled CF across states: Pearson r {np.corrcoef(st.cf_model_own_hub, st.ratio_own_hub)[0, 1]:.2f}; "
          f"against ERA5 100 m speed: {np.corrcoef(st.era5_100m_speed_mean, st.ratio_own_hub)[0, 1]:.2f}")
    si = st[st.group.isin(INTERIOR)]
    print(f"interior states only ({len(si)}): against ERA5 100 m speed, Pearson r {np.corrcoef(si.era5_100m_speed_mean, si.ratio_own_hub)[0, 1]:.2f}")
    print("\nobserved over modeled (own hub) by month (regions, monthly respondents only, capacity-weighted sums of MWh):")
    mrows = []
    pm = pl[pl.monthly]
    for name, states in REGIONS.items():
        g = pm[pm.state.isin(states)] if states else pm[~pm.state.isin([s for v in REGIONS.values() if v for s in v])]
        if len(g) < MIN_PLANTS:
            continue
        ratio = g[list(range(1, 13))].sum() / mon.loc[g.index].sum()
        mrows.append({"group": name, "plants": len(g), **{f"m{m:02d}": round(float(ratio[m]), 3) for m in range(1, 13)}})
    g = pm
    ratio = g[list(range(1, 13))].sum() / mon.loc[g.index].sum()
    mrows.append({"group": "All (monthly respondents)", "plants": len(g), **{f"m{m:02d}": round(float(ratio[m]), 3) for m in range(1, 13)}})
    mdf = pd.DataFrame(mrows)
    mdf.to_csv(HERE / "wind_check_monthly.csv", index=False)
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(mdf.to_string(index=False))
    print(f"runtime {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
