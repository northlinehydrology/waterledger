"""Water use by county: the USGS 2015 estimates for every state, and the reported (or state-estimated) county totals that
Ohio, Texas and Virginia publish. Cached under <cache>/wateruse/. Sources, structure and caveats are in the methods note
docs/methods/water-use-sources.md.

Every layer returns the same shape:

    {"basis": {source, citation, url, year, kind ("estimate" or "reported"), measure ("withdrawals" or "use"), units
               ("Mgal/d"), source_units, threshold, categories (what each category holds in the source), caveats},
     "counties": {county FIPS: {"name", "mgd": {category: Mgal/d}, "ground_mgd": {...}, "surface_mgd": {...},
                                "reuse_mgd": {...} (Texas), "delivered_to_homes_mgd" (USGS), "source_values": {the source's
                                own categories, in its own units}}}}

Categories are a small fixed set (CATEGORIES); a category is left out where the source has no value for it, rather than
written as zero. "total" is the sum of the categories present.

    usgs_2015(state=None)   USGS revised 2015 county estimates (Sleckman, Ross and Cook 2026), any state
    ohio(year=None)         ODNR Water Withdrawal Facility Registration, totaled by county
    texas(year=None)        TWDB Water Use Survey, historical estimates by county (report 7)
    state_layer(state)      the state's own layer, or None where Water Ledger has none
"""
import calendar, csv, datetime, glob, html, io, json, os, re, urllib.parse, urllib.request, zipfile

from waterledger_data.config import CACHE

RAW = os.path.join(CACHE, "wateruse")
CATEGORIES = ("public_supply", "domestic", "commercial", "industrial", "irrigation", "golf", "livestock", "aquaculture", "mining",
              "thermoelectric", "other", "total")
GAL_PER_ACRE_FOOT = 325851.429
UA = "Mozilla/5.0 (waterledger python package; https://waterledger.org)"


def _download(url, path, timeout=300, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".part"
    open(tmp, "wb").write(data)
    os.replace(tmp, path)
    return path


def _days(year):
    return 366 if calendar.isleap(year) else 365


def _r(v, nd=3):
    return round(float(v), nd)


def _total(rec):
    """Add "total" to each per-category dict of a county record (the sum of the categories present)."""
    for k in ("mgd", "ground_mgd", "surface_mgd", "reuse_mgd"):
        if rec.get(k):
            rec[k] = {c: rec[k][c] for c in CATEGORIES if c in rec[k] and c != "total"}
            rec[k]["total"] = _r(sum(rec[k].values()))
    return rec


def county_fips(state):
    """{county name as written by Census ("Franklin County", "Richmond city"): FIPS} and the same keyed by upper-case base
    name ("FRANKLIN"; independent cities as "RICHMOND CITY"), from Census TIGERweb (cached with the state's places)."""
    from waterledger_data import census
    fips = next(f for f, s in _STATES.items() if s == state)
    out = {}
    for f in census._features("county", fips):
        a = f["a"]
        out[a["NAME"]] = a["GEOID"]
        base = a["BASENAME"].upper()
        out[base + " CITY" if a["NAME"].lower().endswith(" city") else base] = a["GEOID"]
    return out


def _names(fips):
    """{FIPS: Census name} from a county_fips() lookup (its mixed-case keys are Census's names)."""
    return {v: k for k, v in fips.items() if not k.isupper()}


# postal codes by state FIPS (as waterledger.states.FIPS; repeated so waterledger_data stays independent of waterledger)
_STATES = {"01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT", "10": "DE", "11": "DC", "12": "FL",
           "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN", "19": "IA", "20": "KS", "21": "KY", "22": "LA", "23": "ME",
           "24": "MD", "25": "MA", "26": "MI", "27": "MN", "28": "MS", "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH",
           "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI",
           "45": "SC", "46": "SD", "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA", "54": "WV", "55": "WI",
           "56": "WY"}


# ---------------------------------------------------------------------------------------------------------------------
# USGS: revised 2015 county estimates, every state

USGS_ITEM = "https://www.sciencebase.gov/catalog/item/683e0ac3d4be0234870fcafe"
USGS_FILES = {"parquet": "all_data_parquet_format.zip", "xlsx": "2015-Revised-County.xlsx"}
USGS_DOI = "10.5066/P14Q6AVK"
# Water Ledger's categories from USGS's category codes. Irrigation is crop plus undifferentiated irrigation (IC + IR), golf
# is IG (IT, irrigation total, = IC + IG + IR); thermoelectric is once-through plus closed-loop cooling (PO + PC).
USGS_CATS = {"public_supply": ("PS",), "domestic": ("DO",), "commercial": ("CO",), "industrial": ("IN",), "irrigation": ("IC", "IR"),
             "golf": ("IG",), "livestock": ("LI",), "aquaculture": ("AQ",), "mining": ("MI",), "thermoelectric": ("PO", "PC")}
USGS_BASIS = {
    "source": "usgs_wu2015", "kind": "estimate", "measure": "withdrawals", "year": 2015, "units": "Mgal/d", "source_units": "Mgal/d",
    "citation": "Sleckman, M.J., Ross, J.C., and Cook, G.L., 2026, Water use data for various spatial scales in the United States, "
                "1985-2015: U.S. Geological Survey data release (2015 revised county estimates)",
    "doi": USGS_DOI, "url": "https://doi.org/" + USGS_DOI, "threshold": None,
    "categories": {"public_supply": "PS", "domestic": "DO (self-supplied)", "commercial": "CO (self-supplied)",
                   "industrial": "IN (self-supplied)", "irrigation": "IC + IR (crop and undifferentiated irrigation)",
                   "golf": "IG (golf course irrigation)", "livestock": "LI", "aquaculture": "AQ", "mining": "MI",
                   "thermoelectric": "PO + PC (once-through and closed-loop cooling)",
                   "total": "the categories present, fresh plus saline, ground plus surface"},
    "caveats": ["USGS estimates for 2015, compiled from state reports and models; not reported values for one facility or year",
                "Withdrawals are counted where water is taken: a county that buys water from a neighbor looks small; "
                "delivered_to_homes_mgd is public supply delivered to homes in the county (DO-PSDel)",
                "Fresh and saline summed; a category is left out where USGS estimated no value",
                "Counties as of 2015 (later boundary changes, such as Connecticut's planning regions, are not mapped)"],
}


def usgs_file():
    """The revised 2015 county table on disk (the parquet from the data release's zip, else the xlsx), downloaded once."""
    d = os.path.join(RAW, "usgs2015")
    pq = os.path.join(d, "2015-Revised-County.parquet")
    if os.path.exists(pq):
        return pq
    xl = os.path.join(d, USGS_FILES["xlsx"])
    if os.path.exists(xl):
        return xl
    item = json.loads(urllib.request.urlopen(urllib.request.Request(USGS_ITEM + "?format=json", headers={"User-Agent": UA}), timeout=60).read())
    links = {f["name"]: f["url"] for f in item.get("files", [])}
    try:
        z = _download(links[USGS_FILES["parquet"]], os.path.join(d, USGS_FILES["parquet"]))
        with zipfile.ZipFile(z) as zf:
            name = next(n for n in zf.namelist() if n.endswith("2015-Revised-County.parquet"))
            open(pq, "wb").write(zf.read(name))
        return pq
    except Exception:                                    # noqa: BLE001  the zip moved or won't read: the same table as xlsx
        return _download(links[USGS_FILES["xlsx"]], xl)


def _usgs_table():
    import pandas as pd
    path = usgs_file()
    df = pd.read_parquet(path) if path.endswith(".parquet") else pd.read_excel(path, dtype={"ST": str, "CO": str})
    df["fips"] = df["ST"].astype(str).str.zfill(2) + df["CO"].astype(str).str.zfill(3)
    return df


def usgs_record(row, columns):
    """One county's record from a row of the USGS table (a dict or Series with the USGS column names)."""
    def val(c):
        v = row.get(c) if hasattr(row, "get") else row[c]
        return None if v is None or v != v else float(v)

    rec = {"name": row["County Name"], "mgd": {}, "ground_mgd": {}, "surface_mgd": {}}
    for cat, codes in USGS_CATS.items():
        parts = {"ground_mgd": [], "surface_mgd": []}
        for code in codes:
            for col in columns:
                if col.startswith(code + "-WGW") or col.startswith(code + "-WSW"):
                    v = val(col)
                    if v is not None:
                        parts["ground_mgd" if "-WGW" in col else "surface_mgd"].append(v)
        if parts["ground_mgd"] or parts["surface_mgd"]:
            g, s = sum(parts["ground_mgd"]), sum(parts["surface_mgd"])
            rec["ground_mgd"][cat], rec["surface_mgd"][cat], rec["mgd"][cat] = _r(g, 2), _r(s, 2), _r(g + s, 2)
    d = val("DO-PSDel")
    rec["delivered_to_homes_mgd"] = _r(d, 2) if d is not None else None
    _total(rec)
    for k in ("mgd", "ground_mgd", "surface_mgd"):
        rec[k]["total"] = _r(rec[k]["total"], 2)
    return rec


def usgs_2015(state=None):
    """USGS revised 2015 county withdrawals (Mgal/d) by category for one state (postal code) or every state."""
    df = _usgs_table()
    if state:
        df = df[df["State"] == state.upper()]
    cols = [c for c in df.columns if "-W" in c]
    return {"basis": USGS_BASIS, "counties": {r["fips"]: usgs_record(r, cols) for r in df.to_dict("records")}}


# ---------------------------------------------------------------------------------------------------------------------
# Ohio: ODNR Water Withdrawal Facility Registration

ODNR = "https://services5.arcgis.com/ajRlmtxbNBjZggOT/arcgis/rest/services/Water_Withdrawal_Facility/FeatureServer"
ODNR_FIRST_YEAR = 2015
# ODNR's primary use (one per facility) -> Water Ledger's category. ODNR's own names are kept in source_values.
OHIO_CATS = {"Public": "public_supply", "Industry": "industrial", "Power": "thermoelectric", "Golf Course": "golf",
             "Agriculture": "irrigation", "Mineral Extraction": "mining", "Hydro Fracturing": "mining", "Misc": "other"}
OHIO_BASIS = {
    "source": "odnr_wwfr", "kind": "reported", "measure": "withdrawals", "units": "Mgal/d", "source_units": "million gallons per year",
    "citation": "Ohio Department of Natural Resources, Division of Water Resources. Water Withdrawal Facility Registration "
                "(annual reports by facility; ArcGIS feature service Water_Withdrawal_Facility)",
    "url": ODNR, "threshold": "facilities able to withdraw 100,000 gallons a day or more register and report each year (ORC 1521.16)",
    "categories": {"public_supply": "Public", "industrial": "Industry", "thermoelectric": "Power", "golf": "Golf Course",
                   "irrigation": "Agriculture (mostly crop, nursery and sod irrigation; a few livestock and poultry farms)",
                   "mining": "Mineral Extraction (mostly quarry dewatering) and Hydro Fracturing; each kept in source_values",
                   "other": "Misc", "total": "every facility in the county, surface plus ground"},
    "caveats": ["One primary use per facility: a facility's whole withdrawal counts in that use",
                "The county is where the facility is, not where its water comes from",
                "Mineral extraction is mostly quarry dewatering, pumped away rather than used",
                "Public-system customers don't register; homes on private wells are not counted",
                "Return flows are reported inconsistently, so consumption is not derived",
                "Million gallons a year converted to Mgal/d over the days in the year"],
}


def _odnr_query(layer, where, fields):
    from waterledger_data.places import _get
    out, off = [], 0
    while True:
        d = _get(f"{ODNR}/{layer}/query", {"where": where, "outFields": fields, "returnGeometry": "false", "orderByFields": "OBJECTID",
                                           "resultOffset": off, "resultRecordCount": 2000, "f": "json"})
        rows = [f["attributes"] for f in d.get("features", [])]
        out += rows
        if not d.get("exceededTransferLimit") and len(rows) < 2000:
            return out
        off += len(rows)


def ohio_raw(refresh=False):
    """ODNR's facilities (layer 0) and annual surface (table 2) and ground (table 3) withdrawals since ODNR_FIRST_YEAR,
    with the date retrieved; cached as wateruse/odnr_registration.json."""
    path = os.path.join(RAW, "odnr_registration.json")
    if refresh or not os.path.exists(path):
        where = f"Year>={ODNR_FIRST_YEAR}"
        raw = {"retrieved": datetime.date.today().isoformat(), "url": ODNR,
               "facilities": _odnr_query(0, "1=1", "RegistrationNumber,Name,CountyName,FacilityPrimaryUseType,Status"),
               "surface": _odnr_query(2, where, "RegistrationNumber,Year,Total"),
               "ground": _odnr_query(3, where, "RegistrationNumber,Year,Total")}
        os.makedirs(RAW, exist_ok=True)
        json.dump(raw, open(path, "w"))
    return json.load(open(path))


def ohio_years(raw=None):
    """{year: facilities reporting}; a year counts as complete when at least 90% as many facilities report as the year before
    (reports for a year arrive the following spring)."""
    raw = raw or ohio_raw()
    n = {}
    for r in raw["surface"] + raw["ground"]:
        n.setdefault(r["Year"], set()).add(r["RegistrationNumber"])
    return {y: len(v) for y, v in sorted(n.items())}


def _latest_complete(counts):
    ys = sorted(counts)
    for y in reversed(ys):
        prev = counts.get(y - 1)
        if prev is None or counts[y] >= 0.9 * prev:
            return y
    return ys[-1]


def ohio(year=None, raw=None, fips=None):
    """ODNR reported withdrawals by county for `year` (default: the latest complete year), in Mgal/d."""
    raw = raw or ohio_raw()
    year = year or _latest_complete(ohio_years(raw))
    fips = fips or county_fips("OH")
    names = _names(fips)
    fac = {f["RegistrationNumber"]: f for f in raw["facilities"]}
    out, unknown = {}, set()
    for part, rows in (("surface_mgd", raw["surface"]), ("ground_mgd", raw["ground"])):
        for r in rows:
            f = fac.get(r["RegistrationNumber"])
            if r["Year"] != year or f is None or not r.get("Total"):
                continue
            cf = fips.get((f["CountyName"] or "").strip().upper())
            if cf is None:
                unknown.add(f["CountyName"])
                continue
            use = f["FacilityPrimaryUseType"] or "Misc"
            rec = out.setdefault(cf, {"name": names.get(cf, f["CountyName"].title() + " County"), "mgd": {}, "ground_mgd": {}, "surface_mgd": {},
                                      "source_values": {}})
            cat = OHIO_CATS.get(use, "other")
            rec[part][cat] = rec[part].get(cat, 0.0) + r["Total"]
            sv = rec["source_values"].setdefault(use, {"surface": 0.0, "ground": 0.0})
            sv["surface" if part == "surface_mgd" else "ground"] += r["Total"]
    if unknown:
        raise ValueError(f"ODNR counties not matched to Census: {sorted(unknown)}")
    days = _days(year)
    for rec in out.values():
        for part in ("surface_mgd", "ground_mgd"):
            rec[part] = {c: v / days for c, v in rec[part].items()}
        rec["mgd"] = {c: _r(rec["surface_mgd"].get(c, 0) + rec["ground_mgd"].get(c, 0)) for c in {*rec["surface_mgd"], *rec["ground_mgd"]}}
        for part in ("surface_mgd", "ground_mgd"):
            rec[part] = {c: _r(v) for c, v in rec[part].items()}
        rec["source_values"] = {u: {k: round(v, 2) for k, v in {**sv, "total": sv["surface"] + sv["ground"]}.items()}
                                for u, sv in sorted(rec["source_values"].items())}
        _total(rec)
    basis = {**OHIO_BASIS, "year": year, "retrieved": raw.get("retrieved")}
    return {"basis": basis, "counties": dict(sorted(out.items()))}


# ---------------------------------------------------------------------------------------------------------------------
# Texas: TWDB Water Use Survey, historical water use estimates by county (SARA report 7)

TWDB_SARA = "https://www3.twdb.texas.gov/apps/SARA/"
TWDB_REPORT = (TWDB_SARA + "ReportViewer/ViewReport.aspx?reportPath=DneA%2Bi0230hTeXN0ZW0uQnl0ZVtdYmR3dFdVX1JFUC9TdW1GaW5hbF9Db3VudHlSZXBvcnRXaXRoUmV1c2U%3D"
               "&lc=RXgzMjAxNzI4NjZ0ZXIxNTY5NzE5M25hbA%3D%3D")
TWDB_YEAR_FIELD = "rptViewer$ctl08$ctl03$ddValue"
TWDB_CATS = {"Municipal": ("public_supply", "Muni"), "Manufacturing": ("industrial", "MFG"), "Mining": ("mining", "Mining"),
             "Power": ("thermoelectric", "Power"), "Irrigation": ("irrigation", "Irrig"), "LiveStock": ("livestock", "Livestock")}
TWDB_BASIS = {
    "source": "twdb_wus", "kind": "estimate", "measure": "use", "units": "Mgal/d", "source_units": "acre-feet per year",
    "citation": "Texas Water Development Board. Historical Water Use Estimates, summary by county with reuse "
                "(Water Use Survey; SARA report 7)",
    "url": "https://www.twdb.texas.gov/waterplanning/waterusesurvey/estimates/", "threshold": None,
    "definitions": "https://www.twdb.texas.gov/waterplanning/waterusesurvey/estimates/doc/WaterUseCategoryDefinition.pdf",
    "categories": {"public_supply": "Municipal: public water systems' intake less sales to other systems and industry, plus "
                                    "TWDB's estimate of self-supplied rural domestic use (data centers are municipal)",
                   "industrial": "Manufacturing (large self-supplied facilities)",
                   "mining": "Mining, including oil and gas (hydraulic fracturing); dewatering only where the water is used",
                   "thermoelectric": "Power (steam-electric): consumptive use only, not withdrawals",
                   "irrigation": "Irrigation, including self-supplied golf courses (estimated by TWDB, not surveyed)",
                   "livestock": "Livestock, including aquaculture (estimated by TWDB, not surveyed)",
                   "total": "the six categories, ground plus surface plus reuse"},
    "caveats": ["TWDB's 'use' is water used in the county, not withdrawals: public systems' intake less their sales to others, "
                "and steam-electric consumption only. Not directly comparable with USGS withdrawals",
                "TWDB's 'historical water use estimates': municipal, manufacturing and power build on TWDB's annual survey of water "
                "systems and plants; rural domestic, irrigation, livestock and oil and gas mining are TWDB estimates. Labeled an "
                "estimate here for that reason",
                "Seawater is not counted; reuse is (reuse_mgd)",
                "Past years are revised as better data arrive (the file records when it was downloaded)",
                "Acre-feet a year converted to Mgal/d over the days in the year"],
}


class SourceUnavailable(RuntimeError):
    """A source's download stopped working (its page or report changed). The message says what to do."""


def fetch_twdb(year=None):
    """Download TWDB's county summary (report 7) for `year` (default: the newest TWDB offers) as CSV, saved as
    wateruse/twdb/county_<year>_<retrieved>.csv. The report sits behind an SSRS viewer (a session, a form post with the
    viewer's tokens, then the CSV export), so this breaks if TWDB changes the page: keep the dated copies."""
    import http.cookiejar
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    op.addheaders = [("User-Agent", "Mozilla/5.0"), ("Referer", TWDB_SARA + "reports/list")]
    step = "the report list"
    try:
        op.open(TWDB_SARA + "reports/list", timeout=120).read()
        step = "the report viewer"
        h = op.open(TWDB_REPORT, timeout=120).read().decode("utf-8", "replace")
        sel = re.search(r'<select name="' + re.escape(TWDB_YEAR_FIELD) + r'".*?</select>', h, re.S)
        opts = {int(lbl): v for v, lbl in re.findall(r'<option[^>]*value="([^"]+)"[^>]*>(\d{4})</option>', sel.group(0))}
        year = year or max(opts)
        if year not in opts:
            raise SourceUnavailable(f"TWDB offers {min(opts)}-{max(opts)}, not {year}")
        form = {k: html.unescape(v) for k, v in re.findall(r'<input type="hidden" name="([^"]+)" id="[^"]*" value="([^"]*)"', h)}
        form[TWDB_YEAR_FIELD] = opts[year]
        form["rptViewer$ctl08$ctl00"] = "View Report"
        act = urllib.parse.urljoin(TWDB_REPORT, html.unescape(re.search(r'<form[^>]*action="([^"]+)"', h).group(1)))
        step = "the year's report"
        h2 = op.open(act, urllib.parse.urlencode(form).encode(), timeout=300).read().decode("utf-8", "replace")
        base = re.search(r'"ExportUrlBase":"([^"]+)"', h2).group(1).encode().decode("unicode_escape")
        step = "the CSV export"
        data = op.open(urllib.parse.urljoin(TWDB_SARA, base) + "CSV", timeout=300).read()
    except SourceUnavailable:
        raise
    except Exception as e:                                   # noqa: BLE001  any change in the viewer lands here
        raise SourceUnavailable(f"TWDB's county water use report could not be downloaded ({step}: {type(e).__name__}: {e}). "
                                f"The SSRS viewer may have changed; download report 7 by hand from {TWDB_SARA}reports/list "
                                f"(Export > CSV) and pass it as texas(path=...), or use a snapshot's carried copy.") from e
    text = data.decode("utf-8-sig", "replace")
    if "CountyName" not in text.split("\n", 1)[0] or f",{year}," not in text:
        raise SourceUnavailable(f"TWDB returned something other than the {year} county CSV; see {TWDB_SARA}reports/list")
    path = os.path.join(RAW, "twdb", f"county_{year}_{datetime.date.today().isoformat()}.csv")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "wb").write(data)
    return path


def twdb_file(year=None, download=True):
    """The newest cached TWDB county CSV for `year` (or for the newest year cached); downloads if there is none."""
    have = sorted(glob.glob(os.path.join(RAW, "twdb", f"county_{year or '[0-9][0-9][0-9][0-9]'}_*.csv")))
    if have:
        return max(have, key=lambda p: os.path.basename(p))
    if not download:
        return None
    return fetch_twdb(year)


def _num(v):
    v = (v or "").strip().replace(",", "")
    return float(v) if v not in ("", "-") else 0.0


def texas(year=None, path=None, fips=None):
    """TWDB water use by county (Mgal/d) from a report 7 CSV (`path`, else the cached or downloaded copy for `year`)."""
    path = path or twdb_file(year)
    rows = list(csv.DictReader(io.StringIO(open(path, encoding="utf-8-sig").read())))
    fips = fips or county_fips("TX")
    yr = int(rows[0]["Year"])
    if year and yr != year:
        raise ValueError(f"{path} holds {yr}, not {year}")
    days, out, names = _days(yr), {}, _names(fips)
    conv = lambda af: _r(af * GAL_PER_ACRE_FOOT / 1e6 / days)
    for r in rows:
        name = r["CountyName"].strip().upper()
        cf = fips.get(name)
        if cf is None:
            raise ValueError(f"TWDB county {name!r} not matched to Census")
        rec = {"name": names.get(cf, name.title() + " County"), "mgd": {}, "ground_mgd": {}, "surface_mgd": {}, "reuse_mgd": {}, "source_values": {}}
        for col, (cat, pre) in TWDB_CATS.items():
            af = {"total": _num(r[col]), "ground": _num(r.get(pre + "_GW") or r.get(pre + "_Gw")), "surface": _num(r[pre + "_SW"]),
                  "reuse": _num(r[pre + "_RU"])}
            rec["source_values"][col] = af
            rec["mgd"][cat] = conv(af["total"])
            rec["ground_mgd"][cat], rec["surface_mgd"][cat], rec["reuse_mgd"][cat] = conv(af["ground"]), conv(af["surface"]), conv(af["reuse"])
        rec["source_values"]["Total"] = {k: sum(v[k] for v in rec["source_values"].values()) for k in ("total", "ground", "surface", "reuse")}
        rec["population"] = int(_num(r["Population"]))
        out[cf] = _total(rec)
    stamp = re.search(r"county_\d{4}_(\d{4}-\d\d-\d\d)\.csv$", os.path.basename(path))
    basis = {**TWDB_BASIS, "year": yr, "retrieved": stamp.group(1) if stamp else None}
    return {"basis": basis, "counties": dict(sorted(out.items()))}


# ---------------------------------------------------------------------------------------------------------------------

STATE_LAYERS = {"OH": ohio, "TX": texas}


def state_layer(state, **kw):
    """The state's own county layer (Ohio, Texas), or None where Water Ledger uses only the USGS estimates."""
    fn = STATE_LAYERS.get(state.upper())
    return fn(**kw) if fn else None
