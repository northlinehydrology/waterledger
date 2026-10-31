"""Michigan's public sources: what `waterledger build-state MI` downloads before it builds. A step whose files are already in the
cache is skipped, so an interrupted build picks up where it stopped. EGLE's water-use file is not here: EGLE refuses scripted
downloads, so a names-removed copy ships in states/mi/inputs/ (see states/mi/egle.py)."""
import datetime, glob, json, os, time, urllib.request

from waterledger_data.config import CACHE


def _fresh(*mods):
    """Forget what earlier steps loaded in this run, so a refetch really goes to the source."""
    for m in mods:
        for v in vars(m).values():
            if hasattr(v, "cache_clear"):
                v.cache_clear()


def echo():
    from waterledger_data import waters as wi
    _fresh(wi)
    wi.potws()


def wellogic():
    from waterledger_data import waters as wi
    _fresh(wi)
    wi.household_wells()


def census():
    from waterledger.states import mi as wl
    from waterledger_data import places as pl
    pl.boundaries(pl.counties())
    pl.municipalities()
    path = os.path.join(wl.RAW_PLACES, "villages_mi.json")
    d = pl._get(f"{pl.TIGER}/Places_CouSub_ConCity_SubMCD/MapServer/4/query",
                {"where": "STATE='26' AND LSADC='47'", "outFields": "BASENAME,GEOID,INTPTLAT,INTPTLON", "returnGeometry": "false", "resultRecordCount": 2000, "f": "json"})
    json.dump([f["attributes"] for f in d["features"]], open(path, "w"))


def water_systems():
    from waterledger_data import places as pl
    cnt = pl.counties()
    pl.enrich(pl.municipalities(), pl.boundaries(cnt))


def attains():
    from waterledger_data import waters as wi
    _fresh(wi)
    for layer in (0, 1, 2):
        rows = wi._paged(f"{wi.ATTAINS}/{layer}/query", "state='MI'", "assessmentunitidentifier,assessmentunitname,ircategory,reportingcycle")
        json.dump({"features": [{"attributes": a} for a in rows]}, open(os.path.join(wi.RAW, f"attains_{layer}_0.json"), "w"))
    wi.attains()
    wi.recode_aus()


def trout():
    from waterledger_data import waters as wi
    _fresh(wi)
    wi.trout_by_huc12()


def mpsc():
    from waterledger_data import power as pw
    pw.territories()


def eia861():
    """EIA posts a year's final EIA-861 the following fall; fetch the newest year that is out and newer than what is on disk."""
    from waterledger_data import power as pw
    try:
        have = pw.eia_year()
    except FileNotFoundError:
        have = 0
    for year in range(datetime.date.today().year - 1, max(have, 2020), -1):
        try:
            pw.fetch_eia861(year)
            return f"EIA-861 {year} downloaded" + (f" (was {have})" if have else "")
        except Exception:
            continue
    return f"EIA-861 {have} is the newest published; nothing to download"


def weather():
    from waterledger.states import mi as wl
    from waterledger_data.climate import hourly_weather
    for rid, r in wl.REGIONS.items():
        for attempt in range(6):
            try:
                hourly_weather(r["lat"], r["lon"], "1995-01-01", "2024-12-31", f"{r.get('cache', rid)}_1995_2024")
                break
            except Exception as e:
                if "429" not in str(e) or attempt == 5:
                    raise
                print(f"  Open-Meteo busy; waiting {60 * (attempt + 1)} s", flush=True)
                time.sleep(60 * (attempt + 1))
        time.sleep(20)


def storms():
    from waterledger_data import places as pl
    pl.county_design_storms(pl.counties())


def precip():
    from waterledger_data import waters as wi
    _fresh(wi)
    wi.county_precip()


def cwns():
    from waterledger_data import waters as wi
    _fresh(wi)
    wi.cwns_design_flows()
    wi.potws()


def wbd():
    from waterledger_data import places as pl
    from waterledger_data import waters as wi
    _fresh(wi)
    pl._layer_polys(6, "huc12,name", "wbd_huc12_mi.json")
    pl._layer_polys(4, "huc8,name", "wbd_huc8_mi.json")
    wi.huc12_links()


def naturalearth():
    from waterledger.states import mi as wl
    base = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"
    for name, f in (("ne_50m_admin_1_states_provinces_lakes.geojson", "adm50.json"), ("ne_50m_lakes.geojson", "lakes50.json")):
        urllib.request.urlretrieve(base + name, os.path.join(wl.RAW_PLACES, f))


def glerl():
    from waterledger.states import mi as wl
    urllib.request.urlretrieve("https://apps.glerl.noaa.gov/erddap/tabledap/glerlLTAvgTemp.csv?lake,dayOfYear,temperature",
                               os.path.join(wl.RAW, "glerl_lt_avg_temp.csv"))


# (step, the files that show it has run, relative to the cache). Order matters: water_systems reads census's files.
STEPS = [(echo, ["waters/echo_potw_mi.json"]), (wellogic, ["waters/wellogic_household_by_township.json"]),
         (census, ["places/counties.json", "places/municipalities.json", "places/boundaries.json", "places/villages_mi.json"]),
         (water_systems, ["places/enrich.json"]),
         (attains, ["waters/attains_[012]_*.json", "waters/attains_table8_mi.json", "waters/attains_stale_au_points.json"]),
         (mpsc, ["power/mpsc_service_areas.json"]), (eia861, ["power/eia861_[0-9][0-9][0-9][0-9]"]), (trout, ["waters/mdnr_trout_streams_mid.json"]),
         (cwns, ["waters/cwns2022_*.csv"]), (weather, ["openmeteo_*_1995_2024.json"]), (storms, ["noaa_pfds_county_*.txt"]),
         (precip, ["waters/noaa_county_precip_1991_2020.json"]), (wbd, ["places/wbd_huc12_mi.json", "places/wbd_huc8_mi.json", "waters/wbd_huc12_tohuc_mi.json"]),
         (naturalearth, ["places/adm50.json", "places/lakes50.json"]), (glerl, ["lit/glerl_lt_avg_temp.csv"])]


def fetch_all(cache=None, tries=3, wait=60):
    """Download every source not yet in the cache, in order; a step that fails is tried again before the build stops."""
    cache = cache or CACHE
    for sub in ("places", "waters", "power", "lit"):
        os.makedirs(os.path.join(cache, sub), exist_ok=True)
    for step, files in STEPS:
        if all(glob.glob(os.path.join(cache, f)) for f in files):
            continue
        for attempt in range(1, tries + 1):
            t0 = time.time()
            print(f"fetch {step.__name__} ...", flush=True)
            try:
                step()
                print(f"  done in {time.time() - t0:,.0f} s", flush=True)
                break
            except Exception as e:
                print(f"  {type(e).__name__}: {e}", flush=True)
                if attempt == tries:
                    raise
                time.sleep(wait * attempt)
