"""Design 0018's check A1: where in its hour AORC's shortwave stands, so the PV chain places the sun right (pv.AORC_SHIFT_S).

    WL_POWER_WORK=~/.cache/waterledger/power_water_work uv run --with "zarr<3" --with "numcodecs<0.16" --with s3fs \
        python docs/methods/power_supply/aorc_timing.py

On a clear day the sun's radiation is symmetric about solar noon. Sampled at each hour's middle, the hourly series' centroid (the
radiation-weighted mean of the hours' times) falls on solar noon; as means over the hour ending at each stamp, 30 minutes after it. So the
median offset of the centroid from solar noon over a year's clear days is the series' own shift, and the PV chain's shift_s is minus it.
Clear days [A]: the day's radiation over the extraterrestrial on the horizontal at least CLEAR. The estimator is checked first on SURFRAD's
measured radiation, averaged both ways (centred, and the hour ending at the stamp: it should give 0 and +30 minutes).

Points: the Clam River (44.30 N, 85.30 W) and the three SURFRAD stations of check A2, 2024 (aorc_points.py; surfrad.py). Writes
aorc_timing.csv next to this file and prints it.
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
POINTS = {"Clam River": (44.30, -85.30), **{f"SURFRAD {k.upper()}": (lat, lon) for k, (_, lat, lon) in surfrad.STATIONS.items()}}
CLEAR = 0.6


def solar_noon(days, lon):
    """UTC solar noon of each UTC date (datetime64[D]), to the minute, from pv.solar_position's equation of time."""
    t = days.astype("datetime64[m]")[:, None] + np.arange(0, 1440)[None, :] - int(round(lon / 15 * 60))   # the local solar day around 12:00
    zen, _ = pv.solar_position(t.ravel(), 45.0, lon)
    return t[np.arange(len(days)), np.argmin(zen.reshape(t.shape), axis=1)]


def offsets(utc, ghi, lat, lon):
    """Each clear day's centroid less solar noon, minutes. Days are local solar days (UTC shifted by the longitude)."""
    ghi = np.nan_to_num(np.asarray(ghi, float))
    local = utc + np.timedelta64(int(round(lon / 15)), "h")
    day = local.astype("datetime64[D]")
    e0h = np.maximum(pv.extraterrestrial(utc) * np.cos(np.radians(pv.solar_position(utc, lat, lon)[0])), 0)
    df = pd.DataFrame({"day": day, "t": (utc - utc[0]).astype(float), "g": ghi, "e": e0h, "ok": np.isfinite(ghi)})
    df["tg"] = df.t * df.g
    s = df.groupby("day").agg(g=("g", "sum"), e=("e", "sum"), tg=("tg", "sum"), n=("ok", "sum"))
    s = s[(s.n == 24) & (s.e > 0) & (s.g / s.e >= CLEAR)]
    centroid = utc[0].astype("datetime64[m]") + np.round(s.tg / s.g * 60).astype(int).values
    noon = solar_noon(s.index.values.astype("datetime64[D]"), lon)
    return (centroid - noon).astype(float)


def row(name, kind, x):
    return {"series": name, "kind": kind, "clear_days": len(x), "offset_min_median": round(float(np.median(x)), 1),
            "offset_min_p25": round(float(np.percentile(x, 25)), 1), "offset_min_p75": round(float(np.percentile(x, 75)), 1),
            "shift_s": int(round(-np.median(x) * 60 / 900) * 900)}


def main():
    rows = []
    for k, (_, lat, lon) in surfrad.STATIONS.items():
        for centred in (True, False):
            t, h = surfrad.hourly(k, YEAR, centred)
            rows.append(row(f"SURFRAD {k.upper()}", "measured, centred" if centred else "measured, hour ending", offsets(t, h["ghi"], lat, lon)))
    a = aorc_points.series(POINTS, YEAR, ("DSWRF_surface",))
    for name, (lat, lon) in POINTS.items():
        rows.append(row(name, "AORC", offsets(a[name]["utc"], a[name]["DSWRF_surface"], lat, lon)))
    out = pd.DataFrame(rows)
    out.to_csv(HERE / "aorc_timing.csv", index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
