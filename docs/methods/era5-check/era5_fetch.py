"""Hourly ERA5 2 m temperature and dew point (C) at the nearest 0.25-degree cells, 1995-01-01 to 2025-01-01 23:00 UTC, from Open-Meteo's
open-data copy of Copernicus ERA5 on AWS (s3://openmeteo/data/copernicus_era5, CC-BY 4.0, anonymous): yearly files to 2021, then
504-hour chunk files (chunk k starts k x 504 hours after 1970-01-01). One JSON per cell, times in UTC.
Usage: python -I era5_fetch.py OUTDIR lat,lon [lat,lon ...]"""
import json, os, sys, time
from concurrent.futures import ThreadPoolExecutor
import fsspec, numpy as np, omfiles

OUT = sys.argv[1]
CELLS = sorted({(round(float(a) * 4), round(float(b) * 4)) for a, b in (p.split(",") for p in sys.argv[2:])})
fs = fsspec.filesystem("s3", anon=True)
H = lambda s: int(np.datetime64(s, "h").astype(np.int64))           # hours since 1970
START, END = H("1995-01-01T00"), H("2025-01-02T00")                 # end exclusive
YEARS = list(range(1995, 2022))
CHUNKS = list(range(H("2022-01-01T00") // 504, (END - 1) // 504 + 1))

def read(var, kind, k, cells):
    path = f"openmeteo/data/copernicus_era5/{var}/" + (f"year_{k}.om" if kind == "year" else f"chunk_{k}.om")
    r = omfiles.OmFileReader.from_fsspec(fs, path)
    t0 = H(f"{k}-01-01T00") if kind == "year" else k * 504
    return var, t0, {c: np.asarray(r[c[0] + 360, c[1] + 720, :], dtype=float) for c in cells}

todo = [c for c in CELLS if not os.path.exists(os.path.join(OUT, f"{c[0] / 4:.2f}_{c[1] / 4:.2f}.json"))]
a = time.perf_counter()
jobs = [(v, "year", y) for v in ("temperature_2m", "dew_point_2m") for y in YEARS] + [(v, "chunk", k) for v in ("temperature_2m", "dew_point_2m") for k in CHUNKS]
with ThreadPoolExecutor(16) as pool:
    got = list(pool.map(lambda j: read(*j, todo), jobs))
for c in todo:
    series = {}
    for var in ("temperature_2m", "dew_point_2m"):
        x = np.full(END - START, np.nan)
        for v, t0, cells in got:
            if v != var:
                continue
            vals = cells[c]
            lo, hi = max(t0, START), min(t0 + len(vals), END)
            if hi > lo:
                x[lo - START:hi - START] = vals[lo - t0:hi - t0]
        series[var] = x
    missing = int(sum(np.isnan(x).sum() for x in series.values()))
    times = [str(np.datetime64(START + h, "h").astype("datetime64[m]"))[:16] for h in range(END - START)]
    json.dump({"latitude": c[0] / 4, "longitude": c[1] / 4, "missing": missing,
               "source": "Copernicus ERA5 via s3://openmeteo/data/copernicus_era5 (CC-BY 4.0), UTC",
               "hourly": {"time": times, **{k: [round(float(v), 2) for v in x] for k, x in series.items()}}},
              open(os.path.join(OUT, f"{c[0] / 4:.2f}_{c[1] / 4:.2f}.json"), "w"))
    print(c, "missing", missing, flush=True)
print(len(todo), "cells in", round(time.perf_counter() - a), "s")
