"""Design 0018's check A4 (and 0014's check 5, hourly shape): when in the day the wind chain makes its energy, against EIA-930's hourly wind
generation for MISO in 2024, in aggregate only.

    export WL_POWER_WORK=~/.cache/waterledger/power_water_work
    uv run --with "zarr<3" --with "numcodecs<0.16" --with s3fs python docs/methods/power_supply/wind_shape_check.py

Observed: EIA-930's net generation from wind for MISO, each hour of 2024 (the six-month BALANCE files, "Adjusted" where given, else as
reported; from July the file splits wind without and with integrated battery storage, summed here), in $WL_POWER_WORK/dl2024. Modeled: the check's wind plants (aorc_check.wind_plants: wind_check.py's plants and screens) whose
balancing authority in EIA-860 2024 is MISO, each at its own hub, summed by nameplate, three ways:

  ERA5            the ERA5 path: 100 m wind at the plant's cell (wind_check.py's cache) to the hub at alpha 0.15 (wind.RANGES' midpoint)
  AORC, table     the AORC path: 10 m wind at the plant's point to the hub by its cell's month-by-hour shear table (aorc_check.py)
  AORC, one alpha the same with one exponent all year, the table's mean at the plant's cell, to show what the table adds
The AORC series run only where AORC's 2024 wind is in the cache at every plant: after design 0018's decision 6 (AORC's 10 m wind steps down in
2018; a study on AORC runs wind on ERA5) the check is the ERA5 path's, which is a study's wind too.

Models give the wind at the hour's stamp; EIA-930's generation is the hour ending at its stamp, so the model's hour is the mean of the stamps at
its ends. Each series is divided by its own mean, so only the shape is compared: the mean by hour of day (Central Standard Time) in each season,
the largest gap from EIA's in any hour, and the hourly correlation over the year. Aggregates only. Writes wind_shape_check.csv next to this file
and prints it.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aorc_check  # noqa: E402
import wind_check  # noqa: E402
from waterledger_models.supply import wind  # noqa: E402

HERE = Path(__file__).resolve().parent
BA = "MISO"
UTC = np.datetime64("2024-01-01T00", "h") + np.arange(8784)
SEASONS = {"winter (DJF)": (12, 1, 2), "spring (MAM)": (3, 4, 5), "summer (JJA)": (6, 7, 8), "fall (SON)": (9, 10, 11)}


def _wind(b, kind):
    """A file's wind generation, MW: the one column, or (from July 2024) the sum of wind without and with integrated battery storage."""
    one = f"Net Generation (MW) from Wind{kind}"
    if one in b.columns:
        return pd.to_numeric(b[one], errors="coerce")
    parts = [pd.to_numeric(b[f"Net Generation (MW) from Wind {w} Integrated Battery Storage{kind}"], errors="coerce") for w in ("without", "with")]
    return parts[0].add(parts[1], fill_value=0.0).where(parts[0].notna() | parts[1].notna())


def observed():
    d = aorc_check.WORK / "dl2024"
    out = []
    for h in ("Jan_Jun", "Jul_Dec"):
        b = pd.read_csv(d / f"EIA930_BALANCE_2024_{h}.csv", low_memory=False, thousands=",")
        b = b[b["Balancing Authority"].eq(BA)]
        t = pd.to_datetime(b["UTC Time at End of Hour"], format="%m/%d/%Y %I:%M:%S %p").values.astype("datetime64[h]")
        out.append(pd.Series(_wind(b, " (Adjusted)").fillna(_wind(b, "")).values, index=t))
    s = pd.concat(out).groupby(level=0).sum(min_count=1)
    return s.reindex(UTC).values


def _hour_ending(x):
    """The hour ending at each stamp from values at the stamps: the mean of the two ends."""
    return np.r_[x[0], 0.5 * (x[1:] + x[:-1])]


def modeled(pl):
    """MW each hour (UTC stamps, hour ending) of the BA's plants, three ways."""
    loss = aorc_check.CENTRAL_WIND["losses"]
    alpha_era5 = sum(wind.RANGES["alpha"]) / 2
    d = aorc_check.WORK / f"aorc_{aorc_check.YEAR}"
    with_aorc = all((d / f"{n}.npz").exists() and "UGRD_10maboveground" in np.load(d / f"{n}.npz").files for n in set(pl.point))
    wx = aorc_check._points(pl.point, aorc_check.WIND_VARS) if with_aorc else {}
    out = {"ERA5": np.zeros(len(UTC))}
    if with_aorc:
        out.update({"AORC, table": np.zeros(len(UTC)), "AORC, one alpha": np.zeros(len(UTC))})
    for _, r in pl.iterrows():
        f = wind_check.WX / f"{r.cell}.npz" if (wind_check.WX / f"{r.cell}.npz").exists() else wind_check.WX_PV / f"{r.cell}.npz"
        z = np.load(f)
        utc = np.datetime64(str(z["start_utc"]), "h") + np.arange(len(z["wind_u_component_100m"]))
        k = np.searchsorted(utc, UTC)
        s100 = np.hypot(z["wind_u_component_100m"], z["wind_v_component_100m"]).astype(float)[k]
        out["ERA5"] += r.mw * wind.power_curve(s100 * (r.hub_m / 100.0) ** alpha_era5) * (1 - loss)
        if not with_aorc:
            continue
        w = wx[r.point]
        if not np.array_equal(w["utc"], UTC):
            raise ValueError("AORC hours differ")
        s10 = np.hypot(w["UGRD_10maboveground"], w["VGRD_10maboveground"])
        tab = np.load(aorc_check.SHEAR_DIR / f"{r.cell}.npy")
        alpha = tab[wind.month(UTC), wind.solar_hour(UTC, r.lon)]
        out["AORC, table"] += r.mw * wind.power_curve(s10 * (r.hub_m / 10.0) ** alpha) * (1 - loss)
        out["AORC, one alpha"] += r.mw * wind.power_curve(s10 * (r.hub_m / 10.0) ** tab.mean()) * (1 - loss)
    return {k: _hour_ending(v) for k, v in out.items()}


def main():
    pl = aorc_check.wind_plants()
    ba = pd.read_excel(aorc_check.WORK / "dl" / "eia860" / "x" / "2___Plant_Y2024.xlsx", header=1).set_index("Plant Code")["Balancing Authority Code"]
    pl = pl[pd.Series(pl.index.map(ba), index=pl.index).astype(str).str.strip().eq(BA)]
    if len(pl) < 5:
        raise ValueError("fewer than five plants")
    obs = observed()
    mod = modeled(pl)
    ok = np.isfinite(obs)
    cst = (UTC - np.timedelta64(6, "h")).astype("datetime64[h]")
    hour = cst.astype("int64") % 24
    mon = cst.astype("datetime64[M]").astype("int64") % 12 + 1
    series = {"EIA-930": obs, **mod}
    norm = {k: v / np.nanmean(v[ok]) for k, v in series.items()}
    rows = []
    for season, ms in SEASONS.items():
        sel = ok & np.isin(mon, ms)
        prof = {k: np.array([v[sel & (hour == h)].mean() for h in range(24)]) / v[sel].mean() for k, v in norm.items()}
        for k, p in prof.items():
            gap = np.abs(p - prof["EIA-930"]).max() if k != "EIA-930" else 0.0
            rows.append({"season": season, "series": k, "night_00_05": round(float(p[0:6].mean()), 3), "day_10_15": round(float(p[10:16].mean()), 3),
                         "night_over_day": round(float(p[0:6].mean() / p[10:16].mean()), 3), "max_hour_gap": round(float(gap), 3),
                         **{f"h{h:02d}": round(float(p[h]), 3) for h in range(24)}})
    for k, v in norm.items():
        rows.append({"season": "year", "series": k, "hourly_corr": round(float(np.corrcoef(v[ok], norm["EIA-930"][ok])[0, 1]), 3),
                     "cf_or_share": round(float(np.nanmean(series[k][ok]) / (pl.mw.sum() if k != "EIA-930" else 1)), 4) if k != "EIA-930" else np.nan})
    out = pd.DataFrame(rows)
    out.insert(2, "plants", len(pl))
    out.insert(3, "mw", round(pl.mw.sum()))
    out.to_csv(HERE / "wind_shape_check.csv", index=False)
    with pd.option_context("display.width", 250, "display.max_columns", 12):
        print(out[["season", "series", "plants", "mw", "night_00_05", "day_10_15", "night_over_day", "max_hour_gap", "hourly_corr",
                   "cf_or_share"]].to_string(index=False))


if __name__ == "__main__":
    main()
