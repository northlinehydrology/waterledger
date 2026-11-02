"""Public climate inputs for a site: hourly weather and NOAA Atlas 14 design-storm depths.

Both are fetched once and cached under engine/data/raw/ (gitignored); rerunning reads the cache.
"""
import ast, json, os, re

from waterledger_data.config import CACHE as RAW
from waterledger_data.fetching import save

# Atlas 14 PFDS rows and columns, in the order the NOAA service returns them
PF_DURATIONS = ["5-min", "10-min", "15-min", "30-min", "60-min", "2-hr", "3-hr", "6-hr", "12-hr", "24-hr",
                "2-day", "3-day", "4-day", "7-day", "10-day", "20-day", "30-day", "45-day", "60-day"]
PF_ARI = [1, 2, 5, 10, 25, 50, 100, 200, 500, 1000]


_fetch = save


def hourly_weather(lat, lon, start, end, name):
    """Hourly 2 m air temperature (C) and relative humidity (%) from the Open-Meteo archive, its best match (ERA5, ERA5-Land and, from 2017, IFS HRES; a reanalysis-based record, not ERA5 alone), in local standard time at the point, for any place.

    Returns (times, temp_c, rh_pct) as lists. Reanalysis smooths local extremes slightly; a full engagement
    cross-checks against NOAA ISD hourly observations at the nearest airport.
    """
    import numpy as np
    a, b = str(np.datetime64(start) - 1), str(np.datetime64(end) + 1)      # a day either side, so every local date asked for is whole
    url = (f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={a}&end_date={b}"
           "&hourly=temperature_2m,relative_humidity_2m&temperature_unit=celsius&timezone=GMT")
    with open(_fetch(url, os.path.join(RAW, f"openmeteo_{name}_utc.json"))) as f:
        h = json.load(f)["hourly"]
    t = np.array(h["time"], dtype="datetime64[m]") + np.timedelta64(round(lon / 15) * 60, "m")     # the rule isd_hourly uses
    days = t.astype("datetime64[D]")
    keep = np.flatnonzero((days >= np.datetime64(start)) & (days <= np.datetime64(end)))
    return [str(x)[:16] for x in t[keep]], [h["temperature_2m"][i] for i in keep], [h["relative_humidity_2m"][i] for i in keep]


POWER_HOURLY = "https://power.larc.nasa.gov/api/temporal/hourly/point"


def power_hourly(lat, lon, name, first=2001, last=2024):
    """Hourly 2 m air temperature (C) and relative humidity (%) from NASA POWER (MERRA-2 reanalysis, 0.5 x 0.625 degree), in local
    standard time, for the states without a hand-built weather set. Free, with no daily quota, so every state can be covered;
    fetched in 8-year pieces (the service's limit per request) and cached. Returns (times, temp_c, rh_pct) like hourly_weather."""
    t, T, RH = [], [], []
    for y0 in range(first, last + 1, 8):
        y1 = min(y0 + 7, last)
        url = (f"{POWER_HOURLY}?parameters=T2M,RH2M&community=RE&longitude={lon:.4f}&latitude={lat:.4f}"
               f"&start={y0}0101&end={y1}1231&format=JSON&time-standard=LST")
        with open(_fetch(url, os.path.join(RAW, "power_hourly", f"{name}_{y0}_{y1}.json"))) as f:
            p = json.load(f)["properties"]["parameter"]
        for k in p["T2M"]:
            a, b = p["T2M"][k], p["RH2M"].get(k)
            if a is None or b is None or a <= -900 or b <= -900:      # -999 marks missing source data
                continue
            t.append(f"{k[:4]}-{k[4:6]}-{k[6:8]}T{k[8:10]}:00")
            T.append(a); RH.append(b)
    return t, T, RH


ISD_HISTORY = "https://www.ncei.noaa.gov/pub/data/noaa/isd-history.csv"
ISD_LITE = "https://noaa-isd-pds.s3.amazonaws.com/isd-lite/data/{y}/{usaf}-{wban}-{y}.gz"


def isd_stations(first=1995, last=2024):
    """US weather stations in NOAA's Integrated Surface Database whose record spans first..last (mostly airports with a WBAN
    number): [{id, name, state, lat, lon}]."""
    import csv
    path = _fetch(ISD_HISTORY, os.path.join(RAW, "isd", "isd-history.csv"))
    out = []
    for r in csv.DictReader(open(path)):
        if r["CTRY"] != "US" or r["WBAN"] == "99999" or not r["LAT"] or not r["BEGIN"]:
            continue
        if r["BEGIN"] > f"{first}0101" or r["END"] < f"{last}1001":
            continue
        out.append({"id": f"{r['USAF']}-{r['WBAN']}", "name": r["STATION NAME"].title(), "state": r["STATE"],
                    "lat": float(r["LAT"]), "lon": float(r["LON"])})
    return out


# Station screens, the same in every state (methods log, Nov 1, 2026). A year counts only with this share of its hours observed, the share the whole record already has to
# reach: Kimble County's 1997 is 2% observed, and filling it from the station's own means would add a year of nothing but average weather. [A]
YEAR_MIN_SHARE = 0.85
# An hour's temperature is suspect this far beyond the 1st to 99th percentile of its month and hour, or this far from both hours beside it. Cold fronts and rain-cooled air
# run further from normal than heat does, so the cold margin is wider. [A] Margins read against 26 stations in OH, VA and TX, and real heat records: see NEIGHBOR_C.
HOT_MARGIN_C, COLD_MARGIN_C, STEP_C = 10.0, 12.0, 8.0
# A suspect hour stands if a nearby station saw much the same then. Margins alone would remove real records: Portland and Seattle in June 2021 were 12 C or more past their
# 99th percentile. Tentative flags reinstated by neighbors are HadISD's approach (Dunn et al. 2012). [A]
NEIGHBOR_KM, NEIGHBORS, NEIGHBOR_C = 150, 3, 8.0
# Dew point drops far further than temperature in a real dry spell (Lubbock and Abilene, June 9, 2020), so its low margin is wide. It goes with the temperature where the report is bad. [A]
DEW_LOW_MARGIN_C = 20.0


def _km(a_lat, a_lon, b_lat, b_lon):
    import math
    dlat, dlon = math.radians(b_lat - a_lat), math.radians(b_lon - a_lon)
    h = math.sin(dlat / 2) ** 2 + math.cos(math.radians(a_lat)) * math.cos(math.radians(b_lat)) * math.sin(dlon / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(h))


def _isd_frame(station, years):
    """A station's reports with both temperature and dew point, in UTC, for `years`: a DataFrame indexed by hour, with T and Td (C)."""
    import gzip
    import pandas as pd
    usaf, wban = station["id"].split("-")
    rows = []
    for y in years:
        path = os.path.join(RAW, "isd", "lite", f"{station['id']}-{y}.gz")
        try:
            _fetch(ISD_LITE.format(y=y, usaf=usaf, wban=wban), path)
        except Exception:
            continue
        with gzip.open(path, "rt") as f:
            for ln in f:
                p = ln.split()
                t, d = int(p[4]), int(p[5])
                if t != -9999 and d != -9999:
                    rows.append((f"{p[0]}-{p[1]}-{p[2]} {p[3]}", t / 10, d / 10))
    if not rows:
        return None
    df = pd.DataFrame(rows, columns=["t", "T", "Td"]).drop_duplicates("t")
    df.index = pd.to_datetime(df.pop("t"))
    return df[~df.index.duplicated()]


def poor_years(observed, min_share=YEAR_MIN_SHARE):
    """The years with too few hours observed. `observed`: a boolean Series by hour, over whole years."""
    share = observed.groupby(observed.index.year).mean()
    return sorted(int(y) for y in share.index[share < min_share])


def _quantile_by_month_hour(x, q):
    return x.groupby([x.index.month, x.index.hour]).transform(lambda v: v.quantile(q))


def _spikes(x, step):
    """Hours further than `step` from both hours beside them, the same way."""
    up, dn = x - x.shift(1), x - x.shift(-1)
    return ((up > step) & (dn > step)) | ((up < -step) & (dn < -step))


def suspect_temperatures(T):
    """Hours whose temperature is suspect: well outside its month and hour's usual range, or a one-hour spike. A boolean Series."""
    return (T > _quantile_by_month_hour(T, 0.99) + HOT_MARGIN_C) | (T < _quantile_by_month_hour(T, 0.01) - COLD_MARGIN_C) | _spikes(T, STEP_C)


def suspect_dew_points(Td):
    return (Td < _quantile_by_month_hour(Td, 0.01) - DEW_LOW_MARGIN_C) | _spikes(Td, STEP_C)


def _neighbor_frames(station, years, first, last):
    """Up to NEIGHBORS other long-record stations within NEIGHBOR_KM, nearest first: their reports for `years`. Fetched only when a station has a suspect hour to check."""
    near = sorted((_km(station["lat"], station["lon"], s["lat"], s["lon"]), s["id"], s) for s in isd_stations(first, last) if s["id"] != station["id"])
    frames = []
    for km, _, s in near[:NEIGHBORS]:
        if km <= NEIGHBOR_KM:
            f = _isd_frame(s, years)
            if f is not None:
                frames.append(f)
    return frames


def unconfirmed(T, suspect, frames):
    """Of the `suspect` hours in T (a Series by hour), those no station in `frames` backs up: none reported within NEIGHBOR_C in that hour or the hours beside it."""
    import pandas as pd
    hours = T.index[suspect]
    bad = pd.Series(True, index=hours)
    for f in frames:
        near = f["T"].reindex(hours, method="nearest", tolerance=pd.Timedelta(hours=1))
        bad &= ~((near - T.reindex(hours)).abs() <= NEIGHBOR_C)
    return bad.index[bad]


def isd_hourly(station, first=1995, last=2024, min_share=0.85, neighbors=None):
    """Hourly 2 m air temperature (C) and relative humidity (%) observed at an ISD station (ISD-Lite: hourly temperature and dew point),
    in local standard time from the station's longitude, for the states without a hand-built weather set. Years with too few hours observed
    are left out (poor_years), and bad readings are screened out (suspect_temperatures, which a nearby station can overrule; suspect_dew_points). Gaps up to 6 hours are
    filled linearly and longer ones with the station's mean for that month and hour, so every day kept has 24 hours. Returns
    (times, temp_c, rh_pct, share_observed, screen), or None when fewer than `min_share` of hours were observed. `screen` says what was removed:
    {"years_left_out", "hours_removed", "dew_points_removed"}, with share_observed the share before screening. `neighbors`, for tests: f(years) -> frames."""
    import numpy as np
    import pandas as pd
    raw = _isd_frame(station, range(first, last + 1))
    if raw is None:
        return None
    full_utc = pd.date_range(f"{first}-01-01 00:00", f"{last}-12-31 23:00", freq="h")
    offset = pd.Timedelta(hours=round(station["lon"] / 15))                                     # UTC to local standard time
    df = raw.copy()
    df.index = df.index + offset
    full = pd.date_range(f"{first}-01-01 00:00", f"{last}-12-31 23:00", freq="h")
    share = float(df.reindex(full)["T"].notna().mean())
    if share < min_share:
        return None
    left_out = poor_years(raw.reindex(full_utc)["T"].notna())
    keep = raw[~raw.index.year.isin(left_out)]
    T = keep["T"].reindex(full_utc[~full_utc.year.isin(left_out)])
    suspect = suspect_temperatures(T)
    removed = pd.DatetimeIndex([])
    if suspect.any():
        years = sorted(set(int(y) for y in T.index[suspect].year))
        removed = unconfirmed(T, suspect, neighbors(years) if neighbors else _neighbor_frames(station, years, first, last))
    keep = keep.copy()
    keep.loc[keep.index.isin(removed), ["T", "Td"]] = np.nan
    bad_dew = suspect_dew_points(keep["Td"].reindex(T.index))
    keep.loc[keep.index.isin(T.index[bad_dew]), "Td"] = np.nan
    screen = {"years_left_out": left_out, "hours_removed": len(removed), "dew_points_removed": int(bad_dew.sum())}
    df = keep.copy()
    df.index = df.index + offset
    df = df.reindex(full)
    df = df.interpolate(limit=6, limit_area="inside")
    clim = df.groupby([df.index.month, df.index.hour]).transform("mean")
    df = df.fillna(clim)
    df = df[~df.index.year.isin(left_out)]
    a = lambda x: np.exp(17.625 * x / (243.04 + x))                       # Magnus form (Alduchov and Eskridge 1996)
    rh = np.clip(100 * a(df["Td"].values) / a(df["T"].values), 1, 100)
    return [i.strftime("%Y-%m-%dT%H:00") for i in df.index], df["T"].tolist(), rh.tolist(), share, screen


def atlas14_depths(lat, lon, name):
    """NOAA Atlas 14 partial-duration precipitation depths (inches) as {duration: {ARI years: depth}}, plus metadata."""
    url = (f"https://hdsc.nws.noaa.gov/cgi-bin/new/cgi_readH5.py?lat={lat:.4f}&lon={lon:.4f}"
           "&type=pf&data=depth&units=english&series=pds")
    with open(_fetch(url, os.path.join(RAW, f"noaa_pfds_{name}.txt"))) as f:
        txt = f.read()
    q = ast.literal_eval(re.search(r"quantiles = (\[.*?\]);", txt, re.S).group(1))
    meta = dict(re.findall(r"^(volume|version|region) = '([^']*)';", txt, re.M))
    return {d: {a: float(v) for a, v in zip(PF_ARI, row)} for d, row in zip(PF_DURATIONS, q)}, meta
