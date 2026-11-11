"""Design 0014's check 5 for PV: the PVWatts chain on ERA5 (supply/pv.py) against EIA's reported output at tracking PV plants, in aggregate only.

    WL_POWER_WORK=~/.cache/waterledger/power_water_work uv run python docs/methods/power_supply/pv_check.py

Input: EIA-860 2024 (3_3_Solar: generators; 2___Plant: latitude and longitude) and EIA-923 2024 (Page 1, net generation), unzipped under
$WL_POWER_WORK/dl/eia860/x and $WL_POWER_WORK/dl/f923. A plant is in the check when every one of its PV generators is operating (status OP),
single-axis tracking and nothing else (no fixed tilt, east-west, dual-axis or concentrating flag), online before January 2024, with no PV
generator retired in 2024 or after, its AC nameplate summed over the generators at least 5 MW (LBNL's utility-scale floor), and its 2024 net
generation for prime mover PV in EIA-923 above zero. AC nameplate is EIA-860's nameplate for PV; the plant's ILR is its DC net capacity over
that nameplate where both are given and the ratio is 1.0-2.0, else pv.py's central 1.3.

Observed: a state's fleet AC capacity factor, the plants' summed 2024 net generation over their summed AC nameplate x 8,784 hours. Modeled:
pv.hourly at the plant's latitude and longitude on its ERA5 cell's 2024 weather (era5.cell's land rule; global and direct horizontal radiation,
2 m temperature, 100 m wind, the hours of 2024 in local standard time as era5.supply keeps them), pv.RANGES' midpoints with resource 1.0 and the
plant's own ILR, capacity-weighted the same way. Also: the modeled fleet at ILR 1.3 for every plant, the fleet without plants that report
storage on site (EIA-860's plant flag), and the resource factor that makes the modeled fleet equal the observed one (pv.output run on a grid
of factors, interpolated). Nothing is tuned.

Aggregates only (design 0014's scope rule): a state is written only with five plants or more. No plant is named or written out. The 2024
weather at the cells is fetched from ERA5's open copy (era5.OPEN_COPY) into $WL_POWER_WORK/pv_check_era5_2024, apart from the raw cache, since
it is one year only. Also by month for four regions (EIA-923's monthly net generation against the model's local-time months), and the fleet without plants whose
own ratio is outside TRIM. Writes pv_check.csv and pv_check_monthly.csv next to this file and prints the tables.
"""
import os, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from waterledger_data import era5
from waterledger_models.supply import pv

HERE = Path(__file__).resolve().parent
WORK = Path(os.environ.get("WL_POWER_WORK", "~/.cache/waterledger/power_water_work")).expanduser()
E860, E923 = WORK / "dl" / "eia860" / "x", WORK / "dl" / "f923"
WX = WORK / "pv_check_era5_2024"
STATES = ("MI", "OH", "IN", "WI", "MN", "IL", "PA", "NY", "VA", "NC", "GA", "FL", "TX", "CO", "AZ", "NV", "CA")
GREAT_LAKES = ("MI", "OH", "IN", "WI", "MN", "IL", "PA", "NY")
MIN_PLANTS, MIN_MW = 5, 5.0
HOURS = 8784                                     # 2024
YEAR = 2024
VARS = ("shortwave_radiation", "direct_radiation", "temperature_2m", "wind_u_component_100m", "wind_v_component_100m")
U0 = np.datetime64(f"{YEAR - 1}-12-31T00", "h")  # UTC, wide enough for local standard time in 2024 anywhere in the states
U1 = np.datetime64(f"{YEAR + 1}-01-01T12", "h")
FACTORS = np.round(np.arange(0.60, 1.101, 0.01), 2)
TRIM = (0.5, 1.2)                                # observed over modeled outside this: a plant out for months or misreported [A]
REGIONS = {"Great Lakes states": GREAT_LAKES, "Southeast (VA, NC, GA, FL)": ("VA", "NC", "GA", "FL"), "Texas": ("TX",),
           "Southwest (CA, AZ, NV, CO)": ("CA", "AZ", "NV", "CO")}
MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")
CENTRAL = {k: (a + b) / 2 for k, (a, b) in pv.RANGES.items()}


def _yes(s):
    return s.astype(str).str.strip().str.upper().eq("Y")


def plants():
    """The check's plants: code, state, lat, lon, ac, ilr, storage. In memory only."""
    x = pd.ExcelFile(E860 / "3_3_Solar_Y2024.xlsx")
    s = pd.read_excel(x, "Operable", header=1)
    r = pd.read_excel(x, "Retired and Canceled", header=1)
    s = s[s["Prime Mover"].eq("PV")].copy()
    s["sat"] = _yes(s["Single-Axis Tracking?"])
    s["other"] = (_yes(s["Fixed Tilt?"]) | _yes(s["Dual-Axis Tracking?"]) | _yes(s["East West Fixed Tilt?"]) | _yes(s["Lenses / Mirrors?"]))
    s["new"] = pd.to_numeric(s["Operating Year"], errors="coerce").fillna(9999) >= YEAR
    s["op"] = s.Status.eq("OP")
    s["ac"] = pd.to_numeric(s["Nameplate Capacity (MW)"], errors="coerce")
    s["dc"] = pd.to_numeric(s["DC Net Capacity (MW)"], errors="coerce")
    s["year"] = pd.to_numeric(s["Operating Year"], errors="coerce")
    retired = set(r.loc[pd.to_numeric(r["Retirement Year"], errors="coerce") >= YEAR, "Plant Code"])
    g = s.groupby("Plant Code").agg(state=("State", "first"), sat=("sat", "all"), other=("other", "any"), new=("new", "any"), op=("op", "all"),
                                    ac=("ac", "sum"), dc=("dc", "sum"), year=("year", "mean"), dc_n=("dc", "count"), n=("ac", "size"))
    g = g[g.sat & ~g.other & ~g.new & g.op & ~g.index.isin(retired) & (g.ac >= MIN_MW) & g.state.isin(STATES)]
    ilr = g.dc / g.ac
    g["ilr"] = np.where((g.dc_n == g.n) & ilr.between(1.0, 2.0), ilr, CENTRAL["ilr"])
    g["ilr_own"] = (g.dc_n == g.n) & ilr.between(1.0, 2.0)
    p = pd.read_excel(E860 / "2___Plant_Y2024.xlsx", header=1).set_index("Plant Code")
    g = g.join(p[["Latitude", "Longitude", "Energy Storage"]].rename(columns={"Latitude": "lat", "Longitude": "lon", "Energy Storage": "storage"}))
    g["storage"] = _yes(g.storage)
    return g.dropna(subset=["lat", "lon"])[["state", "lat", "lon", "ac", "ilr", "ilr_own", "storage", "year"]]


def generation():
    """2024 net generation, MWh, by plant, prime mover PV (EIA-923 Page 1): the year ("gen") and each month (1-12)."""
    f = pd.read_excel(E923 / "EIA923_Schedules_2_3_4_5_M_12_2024_Final.xlsx", "Page 1 Generation and Fuel Data", header=5)
    f = f[f["Reported\nPrime Mover"].eq("PV")]
    cols = {"Net Generation\n(Megawatthours)": "gen", **{f"Netgen\n{m}": i + 1 for i, m in enumerate(MONTHS)}}
    return f[list(cols)].apply(pd.to_numeric, errors="coerce").groupby(f["Plant Id"]).sum().rename(columns=cols)


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
    """{cell: (utc, ghi, beam, t, wind_100m)} for UTC U0..U1, fetched once into WX."""
    WX.mkdir(parents=True, exist_ok=True)
    todo = sorted(c for c in set(cells) if not (WX / f"{c}.npz").exists())
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
        print(f"fetching 2024 weather for {len(todo)} cells: {len(jobs)} reads of up to 40 cell groups")
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
        z = np.load(WX / f"{c}.npz")
        utc = np.datetime64(str(z["start_utc"]), "h") + np.arange(len(z[VARS[0]]))
        lst = utc + np.timedelta64(round(era5.indexes(c)[1] / 4 / 15), "h")
        keep = lst.astype("datetime64[Y]").astype(int) + 1970 == YEAR
        v = {k: z[k].astype(float)[keep] for k in VARS}
        if keep.sum() != HOURS or any(np.isnan(x).any() for x in v.values()):
            raise ValueError(f"ERA5 cell {c}: 2024 hours missing")
        out[c] = (utc[keep], lst[keep].astype("datetime64[M]").astype(int) % 12 + 1, v["shortwave_radiation"], v["direct_radiation"], v["temperature_2m"],
                  np.hypot(v["wind_u_component_100m"], v["wind_v_component_100m"]))
    return out


def model(pl, wx):
    """Each plant's modeled 2024 AC capacity factor: at its own ILR, at ILR 1.3, and at each of FACTORS (own ILR)."""
    own, flat, grid, monthly = [], [], [], []
    for code, row in pl.iterrows():
        utc, month, ghi, beam, t, w = wx[row.cell]
        g = pv.geometry(utc, row.lat, row.lon, "tracking")
        run = lambda **k: float(pv.output(g, ghi, beam, t, w, {**CENTRAL, "ilr": row.ilr, **k}).mean())
        h = pv.output(g, ghi, beam, t, w, {**CENTRAL, "ilr": row.ilr})
        own.append(float(h.mean()))
        monthly.append([float(h[month == m].sum()) * row.ac for m in range(1, 13)])         # MWh
        flat.append(run(ilr=CENTRAL["ilr"]))
        grid.append([run(resource=f) for f in FACTORS])
    pl = pl.assign(cf_model=own, cf_model_ilr13=flat)
    return pl, pd.DataFrame(grid, index=pl.index, columns=FACTORS), pd.DataFrame(monthly, index=pl.index, columns=range(1, 13))


def _row(name, g, grid):
    w = g.ac / g.ac.sum()
    obs = g.gen.sum() / (g.ac.sum() * HOURS)
    mod = float((g.cf_model * w).sum())
    curve = (grid.loc[g.index].mul(w, axis=0)).sum().values                # fleet CF at each factor; rises with the factor
    match = float(np.interp(obs, curve, FACTORS)) if curve[0] <= obs <= curve[-1] else np.nan
    r = g.gen / (g.ac * HOURS) / g.cf_model
    tr = g[r.between(*TRIM)]
    st = g[~g.storage]
    ws = st.ac / st.ac.sum()
    return {"group": name, "plants": len(g), "ac_mw": round(g.ac.sum()), "ilr_mean": round(float((g.ilr * w).sum()), 2),
            "ilr_own_share": round(float(g.ilr_own.mean()), 2), "cf_observed": round(obs, 4), "cf_model": round(mod, 4),
            "ratio_obs_model": round(obs / mod, 3), "cf_model_ilr13": round(float((g.cf_model_ilr13 * w).sum()), 4),
            "plants_no_storage": len(st),
            "ratio_no_storage": round((st.gen.sum() / (st.ac.sum() * HOURS)) / float((st.cf_model * ws).sum()), 3) if len(st) >= MIN_PLANTS else np.nan,
            "plants_trimmed_out": int(len(g) - len(tr)),
            "ratio_trimmed": round((tr.gen.sum() / (tr.ac.sum() * HOURS)) / float((tr.cf_model * tr.ac).sum() / tr.ac.sum()), 3),
            "plant_ratio_p25_p50_p75": "/".join(f"{x:.2f}" for x in r.quantile([0.25, 0.5, 0.75])),
            "online_year_mean": round(float((g.year * w).sum()), 1), "resource_match": round(match, 3)}


def main():
    t0 = time.time()
    pl = plants()
    gen = generation()
    n0 = len(pl)
    pl = pl.join(gen, how="inner")
    pl = pl[pl.gen > 0]
    print(f"plants: {n0} by EIA-860, {len(pl)} with 2024 PV net generation in EIA-923")
    pl["cell"] = [era5.cell(a, b)["id"] for a, b in zip(pl.lat, pl.lon)]
    wx = weather(pl.cell)
    print(f"weather ready at {time.time() - t0:.0f} s ({pl.cell.nunique()} cells)")
    pl, grid, mon = model(pl, wx)
    rows = [_row(s, g, grid) for s, g in pl.groupby("state") if len(g) >= MIN_PLANTS]
    gl = pl[pl.state.isin(GREAT_LAKES)]
    rows.append(_row("Great Lakes states", gl, grid))
    rows.append(_row("All states in the check", pl, grid))
    out = pd.DataFrame(rows)
    out.to_csv(HERE / "pv_check.csv", index=False)
    print(out.to_string(index=False))
    st = out[out.group.str.len() == 2]
    w = st.ac_mw / st.ac_mw.sum()
    print(f"\nstate ratios: capacity-weighted mean {float((st.ratio_obs_model * w).sum()):.3f}, median {st.ratio_obs_model.median():.3f}, "
          f"range {st.ratio_obs_model.min():.3f}-{st.ratio_obs_model.max():.3f}; resource match {st.resource_match.min():.3f}-{st.resource_match.max():.3f}")
    print(f"ratio against modeled CF across states: Pearson r {np.corrcoef(st.cf_model, st.ratio_obs_model)[0, 1]:.2f}")
    print("\nobserved over modeled by month (regions, capacity-weighted sums of MWh):")
    mrows = []
    for name, states in REGIONS.items():
        g = pl[pl.state.isin(states)]
        ratio = g[list(range(1, 13))].sum() / mon.loc[g.index].sum()
        mrows.append({"group": name, "plants": len(g), **{f"m{m:02d}": round(float(ratio[m]), 3) for m in range(1, 13)}})
    mdf = pd.DataFrame(mrows)
    mdf.to_csv(HERE / "pv_check_monthly.csv", index=False)
    print(mdf.to_string(index=False))
    print(f"runtime {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
