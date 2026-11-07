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


# Pieces of one site's record under different IDs: they share a USAF or a WBAN number and stand this close. A site that changed its ID
# (most often WBAN 99999 until 2005, its own WBAN from 2006) has no single ID spanning the period. Quantile mapping, design 0005 (Nov 4, 2026). [A]
# 8 km (was 5, Nov 5): isd-history rounds old pieces' positions, to 0.1 degree for Galveston's 722420-99999, 7 km from its airport's
# current fix; Austin's Camp Mabry and Bergstrom, which share a USAF, are 17 km apart and stay separate.
LINK_KM = 8.0
# The share of the period a site's pieces must cover by isd-history's dates to be tried at all. isd-history's END dates can be early
# (Hobby's 722435-12918 says 1997, its files run to 2010), so this only screens out what can't come close; the 85% of hours decides.
LINK_SPAN_MIN = 0.5


def _span_share(parts, first, last):
    """The share of first..last that `parts` [{begin, end}] (YYYYMMDD) cover between them."""
    import numpy as np
    days = np.arange(np.datetime64(f"{first}-01-01"), np.datetime64(f"{last + 1}-01-01"))
    on = np.zeros(len(days), bool)
    for p in parts:
        b, e = (np.datetime64(f"{x[:4]}-{x[4:6]}-{x[6:]}") for x in (p["begin"], p["end"]))
        on |= (days >= b) & (days <= e)
    return float(on.mean())


def isd_sites(first=1995, last=2024, min_share=0.85):
    """isd_stations, plus the US sites whose record covers first..last only across a change of station ID: pieces sharing a USAF or
    a WBAN number within LINK_KM of each other, between them covering at least LINK_SPAN_MIN of the days by isd-history's dates (the
    85% of hours, isd_hourly's rule, then decides), the newest open to the last year's fall, and at least one with a WBAN. A linked site
    is named after its newest piece and carries `parts` [{id, begin, end}], newest first, which _isd_frame reads in turn; isd_stations'
    own stations are returned as they are.

    Where one of isd_stations' stations is itself a piece of such a group, the linked site is also returned, as its "fallback_for": the
    station with its other IDs filling its gaps, to be used only if the station alone fails the 85% rule (Galveston's 722420-12923 is
    missing 2000-2003, which 722420-99999 has). Its id is the station's with "+linked". `min_share` is kept for callers; unused."""
    import csv
    path = _fetch(ISD_HISTORY, os.path.join(RAW, "isd", "isd-history.csv"))
    rows = [r for r in csv.DictReader(open(path)) if r["CTRY"] == "US" and r["LAT"] and r["BEGIN"] and r["END"] >= f"{first}0101"
            and r["BEGIN"] <= f"{last}1231"]
    up = list(range(len(rows)))

    def root(i):
        while up[i] != i:
            up[i] = up[up[i]]
            i = up[i]
        return i
    by = {}
    for i, r in enumerate(rows):
        for key in (("usaf", r["USAF"]) if r["USAF"] != "999999" else None, ("wban", r["WBAN"]) if r["WBAN"] != "99999" else None):
            if key:
                by.setdefault(key, []).append(i)
    for ids in by.values():
        for a in ids:
            for b in ids:
                if a < b and _km(float(rows[a]["LAT"]), float(rows[a]["LON"]), float(rows[b]["LAT"]), float(rows[b]["LON"])) <= LINK_KM:
                    up[root(b)] = root(a)
    groups = {}
    for i in range(len(rows)):
        groups.setdefault(root(i), []).append(rows[i])
    out = isd_stations(first, last)
    single = {s["id"] for s in out}
    for g in groups.values():
        if len(g) < 2 or all(r["WBAN"] == "99999" for r in g):
            continue
        g = sorted(g, key=lambda r: (r["END"], r["BEGIN"]), reverse=True)
        parts = [{"id": f"{r['USAF']}-{r['WBAN']}", "begin": r["BEGIN"], "end": r["END"]} for r in g]
        if parts[0]["end"] < f"{last}1001" or _span_share(parts, first, last) < LINK_SPAN_MIN:
            continue
        r = g[0]
        site = {"id": parts[0]["id"], "name": r["STATION NAME"].title(), "state": r["STATE"] or next((x["STATE"] for x in g if x["STATE"]), ""),
                "lat": float(r["LAT"]), "lon": float(r["LON"]), "parts": parts}
        spanning = [p["id"] for p in parts if p["id"] in single]
        if spanning:
            site |= {"id": spanning[0] + "+linked", "fallback_for": spanning[0]}
        out.append(site)
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
    """A station's reports with both temperature and dew point, in UTC, for `years`: a DataFrame indexed by hour, with T and Td (C).
    A linked site (isd_sites) reads each of its `parts` for the years it was open, newest first; an hour two parts both report is the newer part's.
    A year no part's isd-history dates cover is tried in every part, since those dates can end early (Hobby's 722435-12918: 1997 listed, files to 2010)."""
    import gzip
    import pandas as pd
    parts = station.get("parts") or [{"id": station["id"], "begin": "0", "end": "9"}]
    listed = lambda part, y: part["begin"][:4] <= str(y) <= part["end"][:4]
    uncovered = {y for y in years if not any(listed(p, y) for p in parts)}
    rows = []
    for part in parts:
        usaf, wban = part["id"].split("-")
        for y in years:
            if not listed(part, y) and y not in uncovered:
                continue
            path = os.path.join(RAW, "isd", "lite", f"{part['id']}-{y}.gz")
            try:
                _fetch(ISD_LITE.format(y=y, usaf=usaf, wban=wban), path, timeout=60, tries=3, wait=20)      # a station's year may be missing: not worth a long wait
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
    return screened_hourly(_isd_frame(station, range(first, last + 1)), station, first, last, min_share, neighbors)


def screened_hourly(raw, station, first=1995, last=2024, min_share=0.85, neighbors=None):
    """isd_hourly's rule on any station's reports: `raw` a DataFrame of T and Td (C) indexed by UTC hour, as _isd_frame and
    _eccc_frame give, `station` its {id, lat, lon}. The neighbors that can overrule a suspect hour are ISD's (_neighbor_frames)."""
    import numpy as np
    import pandas as pd
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



# Environment and Climate Change Canada's hourly station records, read from MSC GeoMet (api.weather.gc.ca) under the ECCC Data Servers
# End-use Licence (version 2.1; open, commercial use allowed, with attribution). Design 0005, Nov 4, 2026.
ECCC_INVENTORY = "https://collaboration.cmc.ec.gc.ca/cmc/climate/Get_More_Data_Plus_de_donnees/Station%20Inventory%20EN.csv"
ECCC_HOURLY = ("https://api.weather.gc.ca/collections/climate-hourly/items?f=csv&limit=10000&CLIMATE_IDENTIFIER={cid}&LOCAL_YEAR={y}"
               "&properties=UTC_DATE,TEMP,TEMP_FLAG,DEW_POINT_TEMP,DEW_POINT_TEMP_FLAG&sortby=UTC_DATE")
ECCC_ATTRIBUTION = "Contains information licenced under the Data Server End-use Licence of Environment and Climate Change Canada."
ECCC_LICENCE = "https://eccc-msc.github.io/open-data/licence/readme_en/"


def eccc_sites(first=1995, last=2024, min_share=0.85):
    """Canadian stations with hourly records covering first..last, as isd_sites gives US ones: [{id, name, state, lat, lon, elev_m, parts}].
    ECCC gives a station a new Climate ID when it moves to automatic reporting or changes hands, and keeps no number across the change,
    so pieces are linked when they stand within LINK_KM and share the first word of their names (Sarnia Airport, Sarnia Chris Hadfield A,
    Sarnia). The pieces' hourly years must cover `min_share` of the period, the newest reaching the last year. `parts` [{id, begin, end}]
    are Climate IDs and hourly years, newest first; the site's id is "eccc-" and its newest Climate ID."""
    import csv
    path = _fetch(ECCC_INVENTORY, os.path.join(RAW, "eccc", "station-inventory.csv"))
    lines = open(path, encoding="utf-8-sig").read().splitlines()
    rows = [r for r in csv.DictReader(lines[3:]) if r["HLY First Year"] and int(r["HLY Last Year"]) >= first and int(r["HLY First Year"]) <= last]
    for r in rows:
        r["lat"], r["lon"] = float(r["Latitude (Decimal Degrees)"]), float(r["Longitude (Decimal Degrees)"])
    up = list(range(len(rows)))

    def root(i):
        while up[i] != i:
            up[i] = up[up[i]]
            i = up[i]
        return i
    first_word = lambda r: r["Name"].split()[0]
    for a in range(len(rows)):
        for b in range(a + 1, len(rows)):
            if first_word(rows[a]) == first_word(rows[b]) and _km(rows[a]["lat"], rows[a]["lon"], rows[b]["lat"], rows[b]["lon"]) <= LINK_KM:
                up[root(b)] = root(a)
    groups = {}
    for i in range(len(rows)):
        groups.setdefault(root(i), []).append(rows[i])
    out = []
    for g in groups.values():
        g = sorted(g, key=lambda r: (int(r["HLY Last Year"]), int(r["HLY First Year"])), reverse=True)
        parts = [{"id": r["Climate ID"], "begin": f"{r['HLY First Year']}0101", "end": f"{r['HLY Last Year']}1231"} for r in g]
        if int(g[0]["HLY Last Year"]) < last or _span_share(parts, first, last) < min_share:
            continue
        r = g[0]
        elev = r["Elevation (m)"]
        out.append({"id": f"eccc-{r['Climate ID']}", "name": r["Name"].title(), "state": r["Province"].title(), "lat": r["lat"], "lon": r["lon"],
                    "elev_m": float(elev) if elev else None, "parts": parts})
    return out


def _eccc_frame(station, years):
    """A Canadian site's hours with both temperature and dew point, in UTC, as _isd_frame gives; each piece of `parts` for the years it
    reported hourly, newest first. A value ECCC flags missing ("M") is left out; its other flags (estimated, accumulated) are kept, as ISD-Lite keeps them."""
    import pandas as pd
    rows = []
    for part in station["parts"]:
        for y in years:
            if not part["begin"][:4] <= str(y) <= part["end"][:4]:
                continue
            path = os.path.join(RAW, "eccc", "hourly", f"{part['id']}-{y}.csv")
            try:
                _fetch(ECCC_HOURLY.format(cid=part["id"], y=y), path, timeout=60, tries=3, wait=20, check=lambda d: d.startswith(b"x,y,UTC_DATE") or d.startswith(b"\xef\xbb\xbfx,y"))
            except Exception:
                continue
            f = pd.read_csv(path, dtype={"TEMP_FLAG": str, "DEW_POINT_TEMP_FLAG": str})
            ok = f["TEMP"].notna() & f["DEW_POINT_TEMP"].notna() & (f["TEMP_FLAG"] != "M") & (f["DEW_POINT_TEMP_FLAG"] != "M")
            rows.append(pd.DataFrame({"t": pd.to_datetime(f["UTC_DATE"][ok]), "T": f["TEMP"][ok].astype(float), "Td": f["DEW_POINT_TEMP"][ok].astype(float)}))
    if not rows:
        return None
    df = pd.concat(rows).drop_duplicates("t")
    df.index = pd.DatetimeIndex(df.pop("t"))
    return df[~df.index.duplicated()].sort_index()


def eccc_hourly(station, first=1995, last=2024, min_share=0.85, neighbors=None):
    """isd_hourly for a Canadian site from eccc_sites: the same share of hours, screens and gap filling, on ECCC's hourly reports."""
    return screened_hourly(_eccc_frame(station, range(first, last + 1)), station, first, last, min_share, neighbors)

def atlas14_depths(lat, lon, name):
    """NOAA Atlas 14 partial-duration precipitation depths (inches) as {duration: {ARI years: depth}}, plus metadata."""
    url = (f"https://hdsc.nws.noaa.gov/cgi-bin/new/cgi_readH5.py?lat={lat:.4f}&lon={lon:.4f}"
           "&type=pf&data=depth&units=english&series=pds")
    with open(_fetch(url, os.path.join(RAW, f"noaa_pfds_{name}.txt"), check=lambda d: b"quantiles" in d)) as f:
        txt = f.read()
    q = ast.literal_eval(re.search(r"quantiles = (\[.*?\]);", txt, re.S).group(1))
    meta = dict(re.findall(r"^(volume|version|region) = '([^']*)';", txt, re.M))
    return {d: {a: float(v) for a, v in zip(PF_ARI, row)} for d, row in zip(PF_DURATIONS, q)}, meta
