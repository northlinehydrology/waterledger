"""Design 0018's check A2: which split of global horizontal radiation into beam and diffuse the AORC path uses, scored at NOAA SURFRAD stations
in the Midwest and Northeast (Bondville IL, Penn State PA, Sioux Falls SD; 2024).

    WL_POWER_WORK=~/.cache/waterledger/power_water_work uv run --with "zarr<3" --with "numcodecs<0.16" --with s3fs \
        python docs/methods/power_supply/split_check.py

Truth: the station's measured global and direct normal radiation, hourly means centred on the stamp (surfrad.py), through the PV chain (a
single-axis tracker at pv.RANGES' midpoints, resource 1.0) with the station's own air temperature and 10 m wind. Two ways for each split
(Erbs, DISC, DIRINT with the dew point, as pv.decompose implements them):

  measured    the split on the station's measured global: the split's own error
  AORC        the split on AORC's global at the station (aorc_points.py, shift 0 by check A1), with AORC's pressure and dew point: the whole
              AORC path; the station's temperature and wind are kept, so only the radiation differs

Also each forcing's global itself against the station's, hour by hour and by day: AORC's (centred hours) and ERA5's at the station's cell
(the open copy, era5.OPEN_COPY; its preceding-hour means against the station averaged over the hour ending at the stamp), to show what the
one-forcing rule costs PV.

Scored over the hours the station measured all three components with the sun above 5 degrees: the beam normal's bias and hourly scatter (RMSE)
against the measured, both as shares of the measured mean, and the same for the PV output; and AORC's global against the measured. The rule
(design 0018, decision 1): DIRINT is used unless it fails to have the smallest hourly PV scatter on the AORC path at all three stations, then
DISC, as NREL's NSRDB used it [A]. Nothing tuned. Writes split_check.csv next to this file and prints it.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aorc_points  # noqa: E402
import surfrad  # noqa: E402
from waterledger_models.supply import pv  # noqa: E402

HERE = Path(__file__).resolve().parent
YEAR = 2024
CENTRAL = {k: (a + b) / 2 for k, (a, b) in pv.RANGES.items()} | {"resource": 1.0}


def dew_point_rh(t_c, rh):
    """Dew point, C, from air temperature and relative humidity (Magnus, Alduchov and Eskridge 1996)."""
    g = np.log(np.clip(rh, 1, 100) / 100) + 17.625 * t_c / (243.04 + t_c)
    return 243.04 * g / (17.625 - g)


def dew_point_q(q, p_pa):
    """Dew point, C, from specific humidity (kg/kg) and pressure (Pa): vapor pressure, then Magnus inverted."""
    e = q * p_pa / (0.622 + 0.378 * q) / 100.0                         # hPa
    g = np.log(np.maximum(e, 1e-3) / 6.1094)
    return 243.04 * g / (17.625 - g)


def score(x, truth, keep):
    m = truth[keep].mean()
    return round(float((x[keep] - truth[keep]).mean() / m), 4), round(float(np.sqrt(((x[keep] - truth[keep]) ** 2).mean()) / m), 4)


def daily_rmse(x, truth, keep, t):
    """Scatter of the days' totals (days with every daylight hour measured), as a share of the mean day."""
    day = t.astype("datetime64[D]")
    df = pd.DataFrame({"d": day, "x": np.where(keep, x, 0.0), "y": np.where(keep, truth, 0.0), "bad": ~keep & (truth > 0)})
    s = df.groupby("d").agg(x=("x", "sum"), y=("y", "sum"), bad=("bad", "sum"))
    s = s[s.bad == 0]
    return round(float(np.sqrt(((s.x - s.y) ** 2).mean()) / s.y.mean()), 4)


def era5_ghi(lat, lon):
    """ERA5's global horizontal radiation at the place's cell over YEAR's UTC hours (preceding-hour means), from the open copy."""
    import fsspec
    import omfiles
    from waterledger_data import era5
    fs = fsspec.filesystem("s3", anon=True)
    i, j = era5.indexes(era5.cell(lat, lon)["id"])
    h0 = int(np.datetime64(f"{YEAR}-01-01T00", "h").astype(np.int64))
    h1 = int(np.datetime64(f"{YEAR + 1}-01-01T00", "h").astype(np.int64))
    x = np.full(h1 - h0, np.nan)
    b = (j + 720) // 6
    for key in range(h0 // 504, (h1 - 1) // 504 + 1):
        r = omfiles.OmFileReader.from_fsspec(fs, f"{era5.OPEN_COPY}/shortwave_radiation/chunk_{key}.om")
        row = np.asarray(r[i + 360, 6 * b:6 * b + 6, :], dtype=float)[j + 720 - 6 * b]
        t0 = key * 504
        lo, hi = max(t0, h0), min(t0 + 504, h1)
        x[lo - h0:hi - h0] = row[lo - t0:hi - t0]
    return x


def global_row(station, forcing, x, k, centred):
    """A forcing's global against the station's: bias and scatter of the hours with either above zero, and of whole measured days."""
    t, h = surfrad.hourly(k, YEAR, centred=centred)
    m = h["ghi"]
    keep = np.isfinite(m) & np.isfinite(x) & ((m > 0) | (x > 0))
    d = pd.DataFrame({"d": t.astype("datetime64[D]"), "x": np.where(keep, x, 0.0), "y": np.where(keep, m, 0.0), "bad": ~np.isfinite(m)})
    s = d.groupby("d").agg(x=("x", "sum"), y=("y", "sum"), bad=("bad", "sum"))
    s = s[s.bad == 0]
    bias, rmse = score(x, m, keep)
    return {"station": station, "way": forcing, "split": "(global itself)", "hours": int(keep.sum()), "global_bias": bias, "global_rmse": rmse,
            "global_rmse_daily": round(float(np.sqrt(((s.x - s.y) ** 2).mean()) / s.y.mean()), 4),
            "global_corr_daily": round(float(np.corrcoef(s.x, s.y)[0, 1]), 3)}


def main():
    rows = []
    a = aorc_points.series({k: (lat, lon) for k, (_, lat, lon) in surfrad.STATIONS.items()}, YEAR)
    for k, (_, lat, lon) in surfrad.STATIONS.items():
        t, h = surfrad.hourly(k, YEAR, centred=True)
        ax = a[k]
        if not np.array_equal(ax["utc"], t):
            raise ValueError(f"{k}: AORC and SURFRAD hours differ")
        g = pv.geometry(t, lat, lon, "tracking", shift_s=0)
        temp = pd.Series(h["temp"]).interpolate(limit_direction="both").values
        wind = pd.Series(h["wind"]).interpolate(limit_direction="both").values
        rh = pd.Series(h["rh"]).interpolate(limit_direction="both").values
        pres = pd.Series(h["pressure"]).interpolate(limit_direction="both").values * 100.0
        keep = np.isfinite(h["ghi"]) & np.isfinite(h["dni"]) & (g["zenith"] < 85)
        ghi_m = np.nan_to_num(h["ghi"])
        dni_m = np.nan_to_num(h["dni"])
        beam_m = np.minimum(dni_m * np.maximum(g["cos_zenith"], 0), ghi_m)
        pv_true = pv._chain(g, ghi_m, beam_m, temp, wind, CENTRAL)
        ghi_a = np.nan_to_num(ax["DSWRF_surface"])
        rows.append(global_row(k.upper(), "AORC", ghi_a, k, True))
        rows.append(global_row(k.upper(), "ERA5", era5_ghi(lat, lon), k, False))
        dew_m, dew_a = dew_point_rh(temp, rh), dew_point_q(ax["SPFH_2maboveground"], ax["PRES_surface"])
        for way, ghi, dew, p in (("measured", ghi_m, dew_m, pres), ("AORC", ghi_a, dew_a, ax["PRES_surface"])):
            for split in pv.SPLITS:
                beam = pv.decompose(g, ghi, split, dew_point=dew if split == "dirint" else None, pressure=p)
                dni = beam / np.maximum(g["cos_zenith"], 1e-6)
                out = pv._chain(g, ghi, beam, temp, wind, CENTRAL)
                b1, r1 = score(dni, dni_m, keep)
                b2, r2 = score(out, pv_true, keep)
                rows.append({"station": k.upper(), "way": way, "split": split, "hours": int(keep.sum()), "beam_normal_bias": b1,
                             "beam_normal_rmse": r1, "pv_bias": b2, "pv_rmse": r2, "pv_rmse_daily": daily_rmse(out, pv_true, keep, t)})
    out = pd.DataFrame(rows)[["station", "way", "split", "hours", "beam_normal_bias", "beam_normal_rmse", "pv_bias", "pv_rmse", "pv_rmse_daily",
                              "global_bias", "global_rmse", "global_rmse_daily", "global_corr_daily"]]
    out.to_csv(HERE / "split_check.csv", index=False)
    with pd.option_context("display.width", 200):
        print(out.to_string(index=False))
    ao = out[(out.way == "AORC") & out.split.isin(pv.SPLITS)]
    best = ao.loc[ao.groupby("station").pv_rmse.idxmin()]
    print("\nsmallest hourly PV scatter on the AORC path, by station:", dict(zip(best.station, best.split)))
    print("DIRINT smallest at all three:", bool((best.split == "dirint").all()))


if __name__ == "__main__":
    main()
