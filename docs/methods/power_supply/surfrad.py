"""NOAA SURFRAD stations' measured radiation, hourly, for design 0018's check A2 (gml.noaa.gov/aftp/data/radiation/surfrad; Augustine et al.
2000, Bull. Amer. Meteor. Soc. 81:2341-2357).

    uv run python docs/methods/power_supply/surfrad.py <year> [bon psu sxf]

Each station's daily files of 1-minute records (UTC): the solar zenith, global (upwelling and downwelling), direct normal and diffuse
radiation, air temperature, humidity, wind at 10 m and pressure, each with a quality flag (0 good). Fetched once into
$WL_POWER_WORK/surfrad/<station>/<year>/. hourly() averages the good minutes in each hour centred on its stamp (minutes -30 to +29), or ending
at it (-60 to -1), and keeps an hour when at least 50 of its minutes are good in all three radiation components [A].
"""
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import urlopen

import numpy as np

BASE = "https://gml.noaa.gov/aftp/data/radiation/surfrad"
WORK = Path(os.environ.get("WL_POWER_WORK", "~/.cache/waterledger/power_water_work")).expanduser()
STATIONS = {"bon": ("Bondville_IL", 40.0519, -88.3731), "psu": ("Penn_State_PA", 40.7201, -77.9309),
            "sxf": ("Sioux_Falls_SD", 43.7340, -96.6233)}
# columns of a record: year jday month day hour min dt zen, then (value, flag) pairs
FIELDS = ("ghi", "up_solar", "dni", "dhi", "dw_ir", "dw_case", "dw_dome", "up_ir", "up_case", "up_dome", "uvb", "par", "net_solar",
          "net_ir", "net", "temp", "rh", "wind", "wind_dir", "pressure")
MIN_GOOD = 50


def _days(year):
    return 366 if year % 4 == 0 else 365


def fetch(station, year, workers=8):
    folder, _, _ = STATIONS[station]
    d = WORK / "surfrad" / station / str(year)
    d.mkdir(parents=True, exist_ok=True)

    def one(doy):
        f = d / f"{station}{year % 100:02d}{doy:03d}.dat"
        if f.exists() and f.stat().st_size > 0:
            return 0
        try:
            with urlopen(f"{BASE}/{folder}/{year}/{f.name}", timeout=60) as r:
                f.write_bytes(r.read())
            return 1
        except Exception:
            return -1

    with ThreadPoolExecutor(workers) as pool:
        got = list(pool.map(one, range(1, _days(year) + 1)))
    return sum(1 for x in got if x == 1), sum(1 for x in got if x == -1)


def minutes(station, year):
    """(utc minute stamps, {field: values with bad flags as NaN}) for the year's files."""
    d = WORK / "surfrad" / station / str(year)
    rows = []
    for f in sorted(d.glob("*.dat")):
        a = np.loadtxt(f, skiprows=2, ndmin=2)
        if a.size:
            rows.append(a)
    a = np.vstack(rows)
    t = (np.array([f"{int(y)}-01-01" for y in a[:, 0]], dtype="datetime64[m]") + ((a[:, 1] - 1) * 1440 + a[:, 4] * 60 + a[:, 5]).astype(int))
    out = {"zen": a[:, 7]}
    for k, name in enumerate(FIELDS):
        v, q = a[:, 8 + 2 * k], a[:, 9 + 2 * k]
        out[name] = np.where((q == 0) & (v > -9000), v, np.nan)
    return t, out


def hourly(station, year, centred=True):
    """Hourly means over the year: (utc hour stamps, {field: mean}), with radiation NaN where fewer than MIN_GOOD minutes are good."""
    t, m = minutes(station, year)
    if centred:                                                        # minutes -30..+29 belong to the hour's stamp
        hour = (t + np.timedelta64(30, "m")).astype("datetime64[h]")
    else:                                                              # minutes -60..-1: the hour ending at the stamp
        hour = t.astype("datetime64[h]") + 1
    h0 = np.datetime64(f"{year}-01-01T00", "h")
    stamps = h0 + np.arange(_days(year) * 24)
    k = (hour - h0).astype(int)
    ok = (k >= 0) & (k < len(stamps))
    out = {}
    rad_ok = np.isfinite(m["ghi"]) & np.isfinite(m["dni"]) & np.isfinite(m["dhi"])
    good = np.bincount(k[ok & rad_ok], minlength=len(stamps))
    for name in ("ghi", "dni", "dhi", "temp", "rh", "wind", "pressure"):
        v = m[name]
        sel = ok & np.isfinite(v) & (rad_ok if name in ("ghi", "dni", "dhi") else True)
        s = np.bincount(k[sel], weights=np.clip(v[sel], 0, None) if name in ("ghi", "dni", "dhi") else v[sel], minlength=len(stamps))
        n = np.bincount(k[sel], minlength=len(stamps))
        mean = np.where(n > 0, s / np.maximum(n, 1), np.nan)
        if name in ("ghi", "dni", "dhi"):
            mean = np.where(good >= MIN_GOOD, mean, np.nan)
        out[name] = mean
    return stamps, out


if __name__ == "__main__":
    yr = int(sys.argv[1])
    for st in sys.argv[2:] or list(STATIONS):
        new, failed = fetch(st, yr)
        print(f"{st} {yr}: {new} files fetched, {failed} not found")
