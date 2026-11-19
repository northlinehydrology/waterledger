"""AORC v1.1 (NOAA's public copy on AWS, s3://noaa-nws-aorc-v1-1-1km, one zarr store a year) at points, hourly, for design 0018's checks.

    uv run --with "zarr<3" --with "numcodecs<0.16" --with s3fs python docs/methods/power_supply/aorc_points.py <year> <name>=<lat>,<lon> ...

The store's chunks are 144 hours x 128 x 256 points (1/120 degree), int16 with a scale of 0.1, zstd-compressed. Points are grouped by the
spatial chunk they fall in, so each chunk is read once for all its points; a year is 61 chunks in time per variable. Each point's series goes to
$WL_POWER_WORK/aorc_<year>/<name>.npz (utc, and each variable in its units: W/m2, m/s, K, Pa, kg/kg), apart from the raw caches since it is for
the checks only. A point is the 1 km cell it falls in (nearest centre). Nothing here is a plant's: a check passes its own points and writes only
aggregates.
"""
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

BUCKET = "noaa-nws-aorc-v1-1-1km"
WORK = Path(os.environ.get("WL_POWER_WORK", "~/.cache/waterledger/power_water_work")).expanduser()
VARS = ("DSWRF_surface", "UGRD_10maboveground", "VGRD_10maboveground", "TMP_2maboveground", "PRES_surface", "SPFH_2maboveground")
LAT0, LON0, STEP = 20.0, -130.0, 1 / 120.0
CHUNK = (144, 128, 256)


def _store(year):
    import s3fs
    import zarr
    return zarr.open_consolidated(s3fs.S3Map(f"{BUCKET}/{year}.zarr", s3=s3fs.S3FileSystem(anon=True)), mode="r")


def index(lat, lon):
    return int(round((lat - LAT0) / STEP)), int(round((lon - LON0) / STEP))


def _read_group(job):
    """One spatial chunk's points, every hour of the year, for one variable: {name: values}."""
    g, var, rows, cols, names_at = job
    a = g[var]
    r0, c0 = min(rows), min(cols)
    block = a.get_orthogonal_selection((slice(None), sorted(set(rows)), sorted(set(cols))))      # time x rows x cols, raw int16
    rs, cs = sorted(set(rows)), sorted(set(cols))
    scale = float(a.attrs.get("scale_factor", 1.0))
    out = {}
    for (r, c), names in names_at.items():
        x = block[:, rs.index(r), cs.index(c)].astype(float)
        x = np.where(x == a.fill_value, np.nan, x * scale)
        for n in names:
            out[n] = x
    del r0, c0
    return var, out


def series(points, year, variables=VARS, workers=16):
    """{name: {"utc": datetime64[h], var: hourly values}} for points {name: (lat, lon)}, fetched once into $WL_POWER_WORK/aorc_<year>."""
    d = WORK / f"aorc_{year}"
    d.mkdir(parents=True, exist_ok=True)
    todo = {n: ll for n, ll in points.items() if not (d / f"{n}.npz").exists()}
    if todo:
        g = _store(year)
        utc = (np.asarray(g["time"][:], dtype="int64") // 3600).astype("datetime64[h]")
        groups = {}
        for n, (lat, lon) in todo.items():
            r, c = index(lat, lon)
            groups.setdefault((r // CHUNK[1], c // CHUNK[2]), {}).setdefault((r, c), []).append(n)
        jobs = [(g, v, [rc[0] for rc in names_at], [rc[1] for rc in names_at], names_at) for v in variables for names_at in groups.values()]
        print(f"AORC {year}: {len(todo)} points in {len(groups)} spatial chunks, {len(jobs)} reads of a year each", flush=True)
        got = {n: {} for n in todo}
        with ThreadPoolExecutor(workers) as pool:
            for k, (var, vals) in enumerate(pool.map(_read_group, jobs), 1):
                for n, x in vals.items():
                    got[n][var] = x
                if k % 20 == 0:
                    print(f"  {k} of {len(jobs)} reads", flush=True)
        for n, v in got.items():
            np.savez_compressed(d / f"{n}.npz", utc=utc.astype("int64"), lat=todo[n][0], lon=todo[n][1], **v)
    out = {}
    for n in points:
        z = np.load(d / f"{n}.npz")
        out[n] = {"utc": z["utc"].astype("datetime64[h]"), **{k: z[k] for k in z.files if k not in ("utc", "lat", "lon")}}
    return out


if __name__ == "__main__":
    yr = int(sys.argv[1])
    pts = {a.split("=")[0]: tuple(float(x) for x in a.split("=")[1].split(",")) for a in sys.argv[2:]}
    for name, s in series(pts, yr).items():
        print(name, len(s["utc"]), {k: round(float(np.nanmean(v)), 2) for k, v in s.items() if k != "utc"})
