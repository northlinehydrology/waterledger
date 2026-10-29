"""Public climate inputs for a site: hourly weather and NOAA Atlas 14 design-storm depths.

Both are fetched once and cached under engine/data/raw/ (gitignored); rerunning reads the cache.
"""
import ast, json, os, re, urllib.request

from waterledger_data.config import CACHE as RAW

# Atlas 14 PFDS rows and columns, in the order the NOAA service returns them
PF_DURATIONS = ["5-min", "10-min", "15-min", "30-min", "60-min", "2-hr", "3-hr", "6-hr", "12-hr", "24-hr",
                "2-day", "3-day", "4-day", "7-day", "10-day", "20-day", "30-day", "45-day", "60-day"]
PF_ARI = [1, 2, 5, 10, 25, 50, 100, 200, 500, 1000]


def _fetch(url, path):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with urllib.request.urlopen(url, timeout=300) as r, open(path, "wb") as f:
            f.write(r.read())
    return path


def hourly_weather(lat, lon, start, end, name):
    """Hourly 2 m air temperature (C) and relative humidity (%) from the Open-Meteo archive (ERA5 reanalysis).

    Returns (times, temp_c, rh_pct) as lists. Reanalysis smooths local extremes slightly; a full engagement
    cross-checks against NOAA ISD hourly observations at the nearest airport.
    """
    url = (f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={start}&end_date={end}"
           "&hourly=temperature_2m,relative_humidity_2m&temperature_unit=celsius&timezone=America%2FDetroit")
    with open(_fetch(url, os.path.join(RAW, f"openmeteo_{name}.json"))) as f:
        h = json.load(f)["hourly"]
    return h["time"], h["temperature_2m"], h["relative_humidity_2m"]


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


def isd_hourly(station, first=1995, last=2024, min_share=0.85):
    """Hourly 2 m air temperature (C) and relative humidity (%) observed at an ISD station (ISD-Lite: hourly temperature and dew point),
    in local standard time from the station's longitude, for the states without a hand-built weather set. Gaps up to 6 hours are
    filled linearly and longer ones with the station's mean for that month and hour, so every day has 24 hours. Returns
    (times, temp_c, rh_pct, share_observed), or None when fewer than `min_share` of hours were observed."""
    import gzip
    import numpy as np
    import pandas as pd
    usaf, wban = station["id"].split("-")
    rows = []
    for y in range(first, last + 1):
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
    df.index = pd.to_datetime(df.pop("t")) + pd.Timedelta(hours=round(station["lon"] / 15))     # UTC to local standard time
    full = pd.date_range(f"{first}-01-01 00:00", f"{last}-12-31 23:00", freq="h")
    df = df[~df.index.duplicated()].reindex(full)
    share = float(df["T"].notna().mean())
    if share < min_share:
        return None
    df = df.interpolate(limit=6, limit_area="inside")
    clim = df.groupby([df.index.month, df.index.hour]).transform("mean")
    df = df.fillna(clim)
    a = lambda x: np.exp(17.625 * x / (243.04 + x))                       # Magnus form (Alduchov and Eskridge 1996)
    rh = np.clip(100 * a(df["Td"].values) / a(df["T"].values), 1, 100)
    return [i.strftime("%Y-%m-%dT%H:00") for i in df.index], df["T"].tolist(), rh.tolist(), share


def atlas14_depths(lat, lon, name):
    """NOAA Atlas 14 partial-duration precipitation depths (inches) as {duration: {ARI years: depth}}, plus metadata."""
    url = (f"https://hdsc.nws.noaa.gov/cgi-bin/new/cgi_readH5.py?lat={lat:.4f}&lon={lon:.4f}"
           "&type=pf&data=depth&units=english&series=pds")
    with open(_fetch(url, os.path.join(RAW, f"noaa_pfds_{name}.txt"))) as f:
        txt = f.read()
    q = ast.literal_eval(re.search(r"quantiles = (\[.*?\]);", txt, re.S).group(1))
    meta = dict(re.findall(r"^(volume|version|region) = '([^']*)';", txt, re.M))
    return {d: {a: float(v) for a, v in zip(PF_ARI, row)} for d, row in zip(PF_DURATIONS, q)}, meta
