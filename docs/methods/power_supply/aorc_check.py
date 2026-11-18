"""Design 0018's check A3: the AORC path (supply.pv.hourly_from_ghi, supply.wind.hourly_from_10m) against EIA's reported 2024 output, in
aggregate only, on the same plants, screens and tables as pv_check.py and wind_check.py (the ERA5 path's check 5); and the resource factors
that set pv.RANGES_AORC. (Its wind part runs where AORC's 2024 wind is cached; after decision 6, a study on AORC runs wind on ERA5, so
fetch takes the PV plants only.)

    export WL_POWER_WORK=~/.cache/waterledger/power_water_work
    uv run --with "zarr<3" --with "numcodecs<0.16" --with s3fs python docs/methods/power_supply/aorc_check.py fetch    # the weather, once
    uv run --with "zarr<3" --with "numcodecs<0.16" --with s3fs python docs/methods/power_supply/aorc_check.py run      # the check

Weather. AORC 2024 at each plant's 1 km point (aorc_points.py; files named by AORC grid index, never by plant): for PV the global
horizontal radiation, 2 m temperature and 10 m wind, for wind the 10 m wind. The shear table at each wind plant's ERA5 cell (era5.cell's land
rule, as est.supply uses it) from ERA5's 10 m and 100 m wind over 2012-2021 [A: ten years, the open copy's yearly files, for the check; a study
sets its table from 1995-2024], read six cells a file as wind_check.py reads, into $WL_POWER_WORK/aorc_check_shear. The hours are 2024's in UTC
[A: EIA's year is local; the difference is a few night hours at each end of the year].

Model, at the RANGES' midpoints with resource 1.0, capacity-weighted as the ERA5 checks are:
  PV     hourly_from_ghi on AORC (shift 0 by check A1, Erbs by check A2), single-axis tracking, the plant's own ILR as pv_check.py takes it
  wind   hourly_from_10m on AORC with the cell's shear table and shear_scale 1, at the 110 m hub (what a study runs for a new project); and at
         the plant's own hub, (hub / 10)^alpha, as wind_check.py's "own hub" composes the curve

Observed over modeled by state (five plants or more), by region and over all; the resource factor that matches each (the chain on a grid of
factors, interpolated); and by month for the regions. The plants' output has each one's balancing authority's 2024 curtailment added back
(curtailment.py, Nov 17, as pv_check.py), since a scenario's dispatch counts curtailment itself; the delivered-basis results of Nov 16 are
kept as aorc_pv_check_delivered.csv and aorc_pv_check_monthly_delivered.csv. Aggregates only (design 0014's scope rule). Writes aorc_pv_check.csv,
aorc_pv_check_monthly.csv, aorc_wind_check.csv and aorc_wind_check_monthly.csv next to this file and prints them.
"""
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aorc_points  # noqa: E402
import curtailment  # noqa: E402
import pv_check  # noqa: E402
import wind_check  # noqa: E402
from waterledger_data import era5  # noqa: E402
from waterledger_models.supply import pv, wind  # noqa: E402

HERE = Path(__file__).resolve().parent
WORK = Path(os.environ.get("WL_POWER_WORK", "~/.cache/waterledger/power_water_work")).expanduser()
SHEAR_DIR = WORK / "aorc_check_shear"
YEAR = 2024
SHEAR_YEARS = range(2012, 2022)
SHEAR_VARS = era5.SHEAR_VARIABLES
PV_VARS = ("DSWRF_surface", "TMP_2maboveground", "UGRD_10maboveground", "VGRD_10maboveground")
WIND_VARS = ("UGRD_10maboveground", "VGRD_10maboveground")
PV_FACTORS = np.round(np.arange(0.60, 1.201, 0.01), 2)
WIND_FACTORS = np.round(np.arange(0.50, 1.501, 0.01), 2)
CENTRAL_PV = {k: (a + b) / 2 for k, (a, b) in pv.RANGES.items()} | {"resource": 1.0}
CENTRAL_WIND = {"shear_scale": 1.0, "losses": (wind.RANGES["losses"][0] + wind.RANGES["losses"][1]) / 2, "resource": 1.0}


def point_name(lat, lon):
    r, c = aorc_points.index(lat, lon)
    return f"r{r}_c{c}"


def pv_plants():
    pl = pv_check.plants().join(pv_check.generation(), how="inner")
    pl = pl[pl.gen > 0].copy()
    pl = curtailment.gross(pl, "solar", pv_check.E860 / "2___Plant_Y2024.xlsx")   # curtailment added back, as pv_check.py (curtailment.py)
    pl["point"] = [point_name(a, b) for a, b in zip(pl.lat, pl.lon)]
    return pl


def wind_plants():
    pl = wind_check.plants().join(wind_check.generation(), how="inner")
    pl = pl[pl.gen > 0].copy()
    pl["point"] = [point_name(a, b) for a, b in zip(pl.lat, pl.lon)]
    pl["cell"] = [era5.cell(a, b)["id"] for a, b in zip(pl.lat, pl.lon)]
    return pl


def _shear_read(job):
    import fsspec
    import omfiles
    var, year, groups = job
    r = omfiles.OmFileReader.from_fsspec(fsspec.filesystem("s3", anon=True), f"{era5.OPEN_COPY}/{var}/year_{year}.om")
    out = {}
    for (i, b), cells in groups:
        row = np.asarray(r[i + 360, 6 * b:6 * b + 6, :], dtype=np.float32)
        for c in cells:
            out[c] = row[era5.indexes(c)[1] + 720 - 6 * b]
    return var, year, out


def fetch_shear(cells, workers=48):
    """Each cell's shear table (12 x 24) from ERA5's 10 m and 100 m wind over SHEAR_YEARS, into SHEAR_DIR/<cell>.npy."""
    SHEAR_DIR.mkdir(parents=True, exist_ok=True)
    todo = sorted(c for c in set(cells) if not (SHEAR_DIR / f"{c}.npy").exists())
    if not todo:
        return
    by = {}
    for c in todo:
        i, j = era5.indexes(c)
        by.setdefault((i, (j + 720) // 6), []).append(c)
    groups = sorted(by.items())
    batches = [groups[k:k + 40] for k in range(0, len(groups), 40)]
    jobs = [(v, y, b) for v in SHEAR_VARS for y in SHEAR_YEARS for b in batches]
    print(f"ERA5 shear: {len(todo)} cells, {len(jobs)} reads", flush=True)
    by_file = {}
    with ThreadPoolExecutor(workers) as pool:
        for var, year, vals in pool.map(_shear_read, jobs):
            by_file.setdefault((var, year), {}).update(vals)
    utc = np.concatenate([np.datetime64(f"{y}-01-01T00", "h") + np.arange(len(by_file[(SHEAR_VARS[0], y)][todo[0]])) for y in SHEAR_YEARS])
    for c in todo:
        u10, v10, u100, v100 = (np.concatenate([by_file[(v, y)][c] for y in SHEAR_YEARS]).astype(float) for v in SHEAR_VARS)
        np.save(SHEAR_DIR / f"{c}.npy", wind.shear_table(utc, era5.indexes(c)[1] / 4.0, u10, v10, u100, v100))


def fetch():
    t0 = time.time()
    pv_pl, wind_pl = pv_plants(), wind_plants()
    print(f"plants: {len(pv_pl)} PV, {len(wind_pl)} wind", flush=True)
    fetch_shear(wind_pl.cell)
    print(f"shear tables ready at {time.time() - t0:.0f} s", flush=True)
    aorc_points.series({p: (a, b) for p, a, b in zip(pv_pl.point, pv_pl.lat, pv_pl.lon)}, YEAR, PV_VARS, workers=24)
    print(f"AORC at the PV plants ready at {time.time() - t0:.0f} s", flush=True)
    if "--wind" in sys.argv:
        aorc_points.series({p: (a, b) for p, a, b in zip(wind_pl.point, wind_pl.lat, wind_pl.lon)}, YEAR, WIND_VARS, workers=24)
        print(f"AORC at the wind plants ready at {time.time() - t0:.0f} s", flush=True)


def _points(names, variables):
    d = WORK / f"aorc_{YEAR}"
    out = {}
    for n in set(names):
        z = np.load(d / f"{n}.npz")
        out[n] = {"utc": z["utc"].astype("datetime64[h]"), **{v: np.nan_to_num(z[v].astype(float)) for v in variables}}
    return out


def pv_model(pl):
    """Each plant's modeled 2024 AC capacity factor (central, own ILR), at each of PV_FACTORS, and by UTC month (MWh)."""
    wx = _points(pl.point, PV_VARS)
    own, grid, monthly = [], [], []
    res = PV_FACTORS[:, None]
    for _, r in pl.iterrows():
        w = wx[r.point]
        g = pv.geometry(w["utc"], r.lat, r.lon, "tracking", shift_s=pv.AORC_SHIFT_S)
        args = (g, w["DSWRF_surface"], w["TMP_2maboveground"] - 273.15, np.hypot(w["UGRD_10maboveground"], w["VGRD_10maboveground"]))
        h = pv.output_from_ghi(*args, {**CENTRAL_PV, "ilr": r.ilr})
        own.append(float(h.mean()))
        mon = w["utc"].astype("datetime64[M]").astype(int) % 12 + 1
        monthly.append([float(h[mon == m].sum()) * r.ac for m in range(1, 13)])
        grid.append(pv.output_from_ghi(*args, {**CENTRAL_PV, "ilr": r.ilr, "resource": res}).mean(axis=1))
    pl = pl.assign(cf_model=own)
    return pl, pd.DataFrame(grid, index=pl.index, columns=PV_FACTORS), pd.DataFrame(monthly, index=pl.index, columns=range(1, 13))


def wind_model(pl):
    """Each plant's modeled 2024 capacity factor at 110 m and at its own hub, at each of WIND_FACTORS, its point's mean 10 m speed, and by
    UTC month at its own hub (MWh)."""
    wx = _points(pl.point, WIND_VARS)
    rows, g110, ghub, monthly = [], [], [], []
    res = WIND_FACTORS[:, None]
    loss = CENTRAL_WIND["losses"]
    for _, r in pl.iterrows():
        w = wx[r.point]
        tab = np.load(SHEAR_DIR / f"{r.cell}.npy")
        u, v = w["UGRD_10maboveground"], w["VGRD_10maboveground"]
        s10 = np.hypot(u, v)
        alpha = tab[wind.month(w["utc"]), wind.solar_hour(w["utc"], r.lon)]
        at = lambda hub, f: wind.power_curve(s10 * f * (hub / 10.0) ** alpha) * (1.0 - loss)
        h110 = wind.hourly_from_10m(w["utc"], r.lon, u, v, tab, CENTRAL_WIND)
        hh = at(r.hub_m, 1.0)
        rows.append((float(h110.mean()), float(hh.mean()), float(s10.mean()), float(alpha.mean())))
        mon = w["utc"].astype("datetime64[M]").astype(int) % 12 + 1
        monthly.append([float(hh[mon == m].sum()) * r.mw for m in range(1, 13)])
        g110.append(wind.hourly_from_10m(w["utc"], r.lon, u, v, tab, {**CENTRAL_WIND, "resource": res}).mean(axis=1))
        ghub.append(at(r.hub_m, res).mean(axis=1))
    pl = pl.assign(cf_110=[a for a, _, _, _ in rows], cf_hub=[b for _, b, _, _ in rows], speed_10=[c for _, _, c, _ in rows],
                   alpha_mean=[d for _, _, _, d in rows])
    return (pl, pd.DataFrame(g110, index=pl.index, columns=WIND_FACTORS), pd.DataFrame(ghub, index=pl.index, columns=WIND_FACTORS),
            pd.DataFrame(monthly, index=pl.index, columns=range(1, 13)))


def _match(g, grid, obs, cap, factors):
    w = g[cap] / g[cap].sum()
    curve = (grid.loc[g.index].mul(w, axis=0)).sum().values
    return float(np.interp(obs, curve, factors)) if curve[0] <= obs <= curve[-1] else np.nan


def pv_row(name, g, grid):
    w = g.ac / g.ac.sum()
    obs = g.gen.sum() / (g.ac.sum() * pv_check.HOURS)
    mod = float((g.cf_model * w).sum())
    r = g.gen / (g.ac * pv_check.HOURS) / g.cf_model
    tr = g[r.between(*pv_check.TRIM)]
    return {"group": name, "plants": len(g), "ac_mw": round(g.ac.sum()), "cf_observed": round(obs, 4), "cf_model_aorc": round(mod, 4),
            "ratio_obs_model": round(obs / mod, 3), "resource_match": round(_match(g, grid, obs, "ac", PV_FACTORS), 3),
            "plants_trimmed_out": int(len(g) - len(tr)),
            "ratio_trimmed": round((tr.gen.sum() / (tr.ac.sum() * pv_check.HOURS)) / float((tr.cf_model * tr.ac).sum() / tr.ac.sum()), 3),
            "plant_ratio_p25_p50_p75": "/".join(f"{x:.2f}" for x in r.quantile([0.25, 0.5, 0.75]))}


def wind_row(name, g, g110, ghub):
    w = g.mw / g.mw.sum()
    obs = g.gen.sum() / (g.mw.sum() * wind_check.HOURS)
    m110, mhub = float((g.cf_110 * w).sum()), float((g.cf_hub * w).sum())
    r = g.gen / (g.mw * wind_check.HOURS) / g.cf_hub
    return {"group": name, "plants": len(g), "mw": round(g.mw.sum()), "hub_m_mean": round(float((g.hub_m * w).sum()), 1),
            "aorc_10m_speed_mean": round(float((g.speed_10 * w).sum()), 2), "shear_alpha_mean": round(float((g.alpha_mean * w).sum()), 3),
            "cf_observed": round(obs, 4), "cf_model_110m": round(m110, 4), "ratio_110m": round(obs / m110, 3),
            "resource_match_110m": round(_match(g, g110, obs, "mw", WIND_FACTORS), 3), "cf_model_own_hub": round(mhub, 4),
            "ratio_own_hub": round(obs / mhub, 3), "resource_match_own_hub": round(_match(g, ghub, obs, "mw", WIND_FACTORS), 3),
            "plant_ratio_own_hub_p25_p50_p75": "/".join(f"{x:.2f}" for x in r.quantile([0.25, 0.5, 0.75]))}


def run():
    t0 = time.time()
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    # PV
    pl, grid, mon = pv_model(pv_plants())
    rows = [pv_row(s, g, grid) for s, g in pl.groupby("state") if len(g) >= pv_check.MIN_PLANTS]
    rows.append(pv_row("Great Lakes states", pl[pl.state.isin(pv_check.GREAT_LAKES)], grid))
    rows.append(pv_row("All states in the check", pl, grid))
    out = pd.DataFrame(rows)
    out.to_csv(HERE / "aorc_pv_check.csv", index=False)
    print(out.to_string(index=False))
    ten = out[(out.group.str.len() == 2) & (out.plants >= 10)]
    print(f"PV resource match, states with 10+ plants ({len(ten)}): {ten.resource_match.min():.3f}-{ten.resource_match.max():.3f}, "
          f"median {ten.resource_match.median():.3f}; overall {out.resource_match.iloc[-1]:.3f}")
    mrows = []
    for name, states in pv_check.REGIONS.items():
        g = pl[pl.state.isin(states)]
        ratio = g[list(range(1, 13))].sum() / mon.loc[g.index].sum()
        mrows.append({"group": name, "plants": len(g), **{f"m{m:02d}": round(float(ratio[m]), 3) for m in range(1, 13)}})
    pd.DataFrame(mrows).to_csv(HERE / "aorc_pv_check_monthly.csv", index=False)
    print(pd.DataFrame(mrows).to_string(index=False))
    print(f"PV done at {time.time() - t0:.0f} s\n", flush=True)
    # wind, where AORC's 2024 wind is cached at every plant (after decision 6 it is not fetched: AORC's 10 m wind steps down in 2018)
    wpl = wind_plants()
    d = WORK / f"aorc_{YEAR}"
    if not all((d / f"{n}.npz").exists() for n in set(wpl.point)):
        print("AORC wind not fetched (design 0018, decision 6): the wind part is skipped")
        return
    pl, g110, ghub, mon = wind_model(wpl)
    rows = [wind_row(s, g, g110, ghub) for s, g in pl.groupby("state") if len(g) >= wind_check.MIN_PLANTS]
    for name, states in wind_check.REGIONS.items():
        g = pl[pl.state.isin(states)] if states else pl[~pl.state.isin([s for v in wind_check.REGIONS.values() if v for s in v])]
        if len(g) >= wind_check.MIN_PLANTS:
            rows.append(wind_row(name, g, g110, ghub))
    interior = pl[pl.state.isin(wind_check.INTERIOR)]
    rows.append(wind_row(wind_check.INTERIOR_NAME, interior, g110, ghub))
    for lo, hi in ((0, 3.0), (3.0, 4.0), (4.0, 5.0), (5.0, 99)):
        g = pl[pl.speed_10.between(lo, hi, inclusive="left")]
        if len(g) >= wind_check.MIN_PLANTS:
            rows.append(wind_row(f"AORC 10 m mean speed {lo}-{hi} m/s", g, g110, ghub))
    rows.append(wind_row("All plants in the check", pl, g110, ghub))
    out = pd.DataFrame(rows)
    out.to_csv(HERE / "aorc_wind_check.csv", index=False)
    print(out.to_string(index=False))
    ten = out[(out.group.str.len() == 2) & (out.plants >= 10)]
    tin = ten[ten.group.isin(wind_check.INTERIOR)]
    for col in ("resource_match_110m", "resource_match_own_hub"):
        print(f"wind {col}: states with 10+ plants {ten[col].min():.3f}-{ten[col].max():.3f} (median {ten[col].median():.3f}); interior "
              f"{tin[col].min():.3f}-{tin[col].max():.3f} (median {tin[col].median():.3f}); overall {out[col].iloc[-1]:.3f}")
    mrows = []
    pm = pl[pl.monthly]
    for name, states in wind_check.REGIONS.items():
        g = pm[pm.state.isin(states)] if states else pm[~pm.state.isin([s for v in wind_check.REGIONS.values() if v for s in v])]
        if len(g) < wind_check.MIN_PLANTS:
            continue
        ratio = g[list(range(1, 13))].sum() / mon.loc[g.index].sum()
        mrows.append({"group": name, "plants": len(g), **{f"m{m:02d}": round(float(ratio[m]), 3) for m in range(1, 13)}})
    pd.DataFrame(mrows).to_csv(HERE / "aorc_wind_check_monthly.csv", index=False)
    print(pd.DataFrame(mrows).to_string(index=False))
    print(f"runtime {time.time() - t0:.0f} s")


if __name__ == "__main__":
    {"fetch": fetch, "run": run}[sys.argv[1]]()
