"""Michigan receiving waters and sewer plants, cached under engine/data/raw/waters/.

Sources (all public):
  EPA ATTAINS        2026 Integrated Report assessment units and parameters for Michigan (EGLE's 303(d)/305(b) listings),
                     via the ATTAINS_Assessment map service (no key needed)
  USGS WBD           HUC12 downstream links (tohuc), via The National Map REST
  NOAA NCEI          county annual precipitation, 1991-2020 mean (Climate at a Glance, nClimGrid)
  EPA ECHO           Michigan sewer plants (POTWs): location, receiving water, combined sewer flag, last year's average flow
"""
import collections, functools, glob, json, os, re, urllib.parse, urllib.request

from waterledger_data.config import CACHE

RAW = os.path.join(CACHE, "waters")
ATTAINS = "https://gispub.epa.gov/arcgis/rest/services/OW/ATTAINS_Assessment/MapServer"
WBD6 = "https://hydro.nationalmap.gov/arcgis/rest/services/wbd/MapServer/6/query"
ECHO = "https://echodata.epa.gov/echo/cwa_rest_services"

# ATTAINS parameter groups -> plain groups. Runoff and wastewater can add to the first set; the "fish" group is legacy
# contamination (mercury, PCBs, PFAS in fish tissue) that a new campus would not change much.
GROUPS = {
    "SEDIMENT": "sed", "TURBIDITY": "sed",
    "CAUSE UNKNOWN - IMPAIRED BIOTA": "bio", "CAUSE UNKNOWN": "bio",
    "NUTRIENTS": "nut", "ALGAL GROWTH": "nut", "NOXIOUS AQUATIC PLANTS": "nut",
    "ORGANIC ENRICHMENT/OXYGEN DEPLETION": "do",
    "PATHOGENS": "ecoli",
    "TEMPERATURE": "temp",
    "SALINITY/TOTAL DISSOLVED SOLIDS/CHLORIDES/SULFATES": "salt",
    "HYDROLOGIC ALTERATION": "flow", "HABITAT ALTERATIONS": "flow",
    "OIL AND GREASE": "oil",
    "METALS (OTHER THAN MERCURY)": "metal", "PH/ACIDITY/CAUSTIC CONDITIONS": "metal",
    "MERCURY": "fish", "POLYCHLORINATED BIPHENYLS (PCBS)": "fish", "PER- AND POLYFLUOROALKYL SUBSTANCES (PFAS)": "fish",
    "DIOXINS": "fish", "PESTICIDES": "fish", "TOXIC ORGANICS": "fish", "TOTAL TOXICS": "fish",
}
LABELS = {
    "sed": "Sediment", "bio": "Fish and stream insects in poor shape", "nut": "Phosphorus and algae", "do": "Low oxygen",
    "ecoli": "Bacteria (E. coli)", "temp": "Water too warm", "salt": "Salt (chloride)", "flow": "Flow and habitat changes",
    "oil": "Oil and grease", "metal": "Metals", "fish": "Chemicals in fish (mercury, PCBs, PFAS)",
}
ORDER = ["sed", "nut", "temp", "salt", "do", "bio", "flow", "ecoli", "oil", "metal", "fish"]


def _get(url, params, timeout=180):
    with urllib.request.urlopen(url + "?" + urllib.parse.urlencode(params), timeout=timeout) as r:
        return json.load(r)


def _paged(url, where, fields="*", page=2000):
    rows, off = [], 0
    while True:
        d = _get(url, {"where": where, "outFields": fields, "returnGeometry": "false", "resultOffset": off,
                       "resultRecordCount": page, "orderByFields": "OBJECTID" if "ATTAINS" in url else "huc12", "f": "json"})
        rows += [f["attributes"] for f in d.get("features", [])]
        if len(d.get("features", [])) < page:
            return rows
        off += page


def _cached(name, fn):
    path = os.path.join(RAW, name)
    if not os.path.exists(path):
        os.makedirs(RAW, exist_ok=True)
        json.dump(fn(), open(path, "w"))
    return json.load(open(path))


def attains():
    """Michigan assessment units (names, categories) and their parameters, 2026 cycle."""
    aus = {}
    for p in sorted(glob.glob(os.path.join(RAW, "attains_[012]_*.json"))):
        for f in json.load(open(p))["features"]:
            a = f["attributes"]
            aus[a["assessmentunitidentifier"]] = {"name": a["assessmentunitname"], "cat": a["ircategory"], "cycle": a["reportingcycle"]}
    if not aus:
        for layer in (0, 1, 2):
            for a in _paged(f"{ATTAINS}/{layer}/query", "state='MI'", "assessmentunitidentifier,assessmentunitname,ircategory,reportingcycle"):
                aus[a["assessmentunitidentifier"]] = {"name": a["assessmentunitname"], "cat": a["ircategory"], "cycle": a["reportingcycle"]}
    params = _cached("attains_table8_mi.json", lambda: _paged(f"{ATTAINS}/8/query", "organizationid='21MICH'"))
    return aus, params


@functools.lru_cache(None)
def huc12_links():
    return {r["huc12"]: r for r in _cached("wbd_huc12_tohuc_mi.json", lambda: _paged(WBD6, "states LIKE '%MI%'", "huc12,name,tohuc,hutype", 1000))}


@functools.lru_cache(None)
def county_precip():
    def fetch():
        out = {}
        for i in range(1, 166, 2):
            d = _get(f"https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/county/time-series/MI-{i:03d}/pcp/12/12/1991-2020/data.json", {})
            v = [x["value"] for x in d["data"].values()]
            out[f"26{i:03d}"] = {"name": d["description"]["title"].split(",")[0], "annual_in": round(sum(v) / len(v), 2), "n": len(v)}
        return {"source": "NOAA NCEI Climate at a Glance, county time series (nClimGrid), January-December precipitation, mean 1991-2020", "counties": out}
    return {k: v["annual_in"] for k, v in _cached("noaa_county_precip_1991_2020.json", fetch)["counties"].items()}


@functools.lru_cache(None)
def by_huc12():
    """Impairments of the waters in each HUC12 (assessment units whose ID carries that HUC12), with whether a TMDL covers each,
    plus the downstream HUC12 so the client can follow the water. Returns {huc12: {"n": name, "t": tohuc, "i": [[group, tmdl, waters]]}}."""
    aus, params = attains()
    links = huc12_links()
    found = collections.defaultdict(lambda: collections.defaultdict(lambda: {"tmdl": 0, "w": set()}))
    recoded = recode_aus()
    for r in params:
        if r["parameterstatus"] not in ("Cause", "Observed effect"):
            continue
        g = GROUPS.get(r["parametergroupname"])
        m = re.match(r"MI(\d{12})", r["assessmentunitidentifier"] or "")
        if not g or not m:
            continue
        e = found[recoded.get(r["assessmentunitidentifier"], m.group(1))][g]
        e["tmdl"] |= int(r["parametercategorycode"] == "4A")
        name = aus.get(r["assessmentunitidentifier"], {}).get("name") or ""
        if name and " in HUC " not in name:   # named lakes and rivers; generic "Rivers/Streams in HUC ..." units go unnamed
            e["w"].add(name.title() if name.isupper() else name)
    assessed = {recoded.get(a, re.match(r"MI(\d{12})", a).group(1)) for a, v in aus.items()
                if re.match(r"MI(\d{12})", a) and not a.endswith(("-NA", "-NAL"))}
    out = {}
    for h, L in links.items():
        rec = {"n": L["name"], "t": L["tohuc"] if L["tohuc"] in links else None, "a": int(h in assessed)}
        if h in found:
            rec["i"] = [[g, found[h][g]["tmdl"], sorted(found[h][g]["w"])[:3]] for g in ORDER if g in found[h]]
        out[h] = rec
    return out


ECHO_COLS = "1,2,4,13,15,26,27,28,29,30,31,53,56,62,150,158,159,161,168,172,173,175,176,178,179"


@functools.lru_cache(None)
def potws():
    """Michigan wastewater plants from EPA's Clean Watersheds Needs Survey 2022 (design flow, location; includes lagoons and plants that
    discharge to groundwater under state permits), with last year's average reported flow, receiving water and combined-sewer status
    from EPA ECHO where an NPDES permit matches. ECHO flows that don't fit the plant's design flow are dropped (unit errors are common)."""
    import csv

    def fetch():
        q = _get(f"{ECHO}.get_facilities", {"output": "JSON", "p_st": "MI", "p_pcomp": "POT", "responseset": 1000})["Results"]["QueryID"]
        return _get(f"{ECHO}.get_qid", {"output": "JSON", "qid": q, "pageno": 1, "responseset": 1000, "qcolumns": ECHO_COLS})["Results"]["Facilities"]
    rows = _cached("echo_potw_mi.json", lambda: {"Results": {"Facilities": fetch()}})
    rows = rows["Results"]["Facilities"] if isinstance(rows, dict) else rows
    echo = {r["SourceID"]: r for r in rows if r["CWPPermitStatusDesc"] not in ("Terminated", "Expired")}
    cwns_design_flows()   # downloads the CWNS tables if needed
    for f in ("FACILITIES", "PHYSICAL_LOCATION"):
        path = os.path.join(RAW, f"cwns2022_{f}.csv")
        if not os.path.exists(path):
            urllib.request.urlretrieve(f"{CWNS}/{f}.csv", path)
    rd = lambda f: csv.DictReader(open(os.path.join(RAW, f"cwns2022_{f}.csv")))
    fac = {r["CWNS_ID"]: r for r in rd("FACILITIES") if r["STATE_CODE"] == "MI" and r["INFRASTRUCTURE_TYPE"] == "Wastewater"}
    flow = {r["CWNS_ID"]: float(r["CURRENT_DESIGN_FLOW"]) for r in rd("FLOW") if r["STATE_CODE"] == "MI" and r["FLOW_TYPE"] == "Total Flow" and r["CURRENT_DESIGN_FLOW"]}
    loc = {r["CWNS_ID"]: r for r in rd("PHYSICAL_LOCATION") if r["STATE_CODE"] == "MI" and r["LATITUDE"]}
    permits = collections.defaultdict(list)
    for r in rd("FACILITY_PERMIT"):
        if r["STATE_CODE"] == "MI":
            permits[r["CWNS_ID"]].append(r["PERMIT_NUMBER"])
    out = []
    for cid, fr in fac.items():
        if cid not in flow or cid not in loc:
            continue
        e = next((echo[pm] for pm in permits[cid] if pm in echo), None)
        design = flow[cid]
        f_echo = float(e["PastCalYrAverageFlow"]) if e and e["PastCalYrAverageFlow"] else None
        if f_echo and not 0.1 <= f_echo / design <= 1.3:
            f_echo = None
        name = fr["FACILITY_NAME"].upper()
        out.append({"id": (e or {}).get("SourceID") or (permits[cid] or [cid])[0], "name": name, "city": loc[cid]["CITY"],
                    "lat": float(loc[cid]["LATITUDE"]), "lon": float(loc[cid]["LONGITUDE"]),
                    "major": bool(e and e["CWPMajorMinorStatusFlag"] == "M"), "cso": bool(e and e["CWPCsoFlag"] == "Y"), "flow_mgd": f_echo, "design_mgd": design,
                    "receiving": (e or {}).get("CWPStateWaterBodyName"), "huc12": (e or {}).get("RadWBDHuc12"),
                    "lagoon": bool(re.search(r"LAGOON|WWSL|STABILIZATION", name))})
    return out


TROUT = "https://services3.arcgis.com/Jdnp1TjADvSDxMAX/ArcGIS/rest/services/DNRFisheriesTroutRegsOPENDATA/FeatureServer/0/query"


@functools.lru_cache(None)
def trout_by_huc12():
    """Designated trout streams (coldwater under R 323.1100(7)) per HUC12: number of designated segments whose midpoint falls inside
    the HUC12 and a few stream names. Michigan DNR's layer; it lists only streams classified by type, so it can miss some designated waters."""
    from waterledger_data import places as pl

    def fetch():
        out, off = [], 0
        while True:
            d = _get(TROUT, {"where": "Designated=1 AND isActive=1", "outFields": "DNRName,StreamType", "outSR": 4326, "geometryPrecision": 4,
                             "maxAllowableOffset": 0.002, "resultOffset": off, "resultRecordCount": 2000, "orderByFields": "OBJECTID", "f": "json"}, 300)
            for f in d["features"]:
                pts = [p for path in (f.get("geometry") or {}).get("paths", []) for p in path]
                if pts:
                    out.append({"name": f["attributes"]["DNRName"], "type": f["attributes"]["StreamType"], "mid": pts[len(pts) // 2], "len": len(pts)})
            if len(d["features"]) < 2000:
                return {"source": "Michigan DNR, Trout and Salmon Regulations Stream Main, Designated=1 and isActive=1; segment midpoints", "segments": out}
            off += 2000
    segs = _cached("mdnr_trout_streams_mid.json", fetch)["segments"]
    polys = pl._layer_polys(6, "huc12,name", "wbd_huc12_mi.json")
    out = {}
    for s in segs:
        x, y = s["mid"]
        for q in polys:
            b = q["bbox"]
            if b[0] <= x <= b[2] and b[1] <= y <= b[3] and pl._inside(x, y, q["rings"]):
                e = out.setdefault(q["huc12"], {"n": 0, "names": set()})
                e["n"] += 1
                if s["name"]:
                    e["names"].add(s["name"])
                break
    return {h: {"n": e["n"], "names": sorted(e["names"])[:3]} for h, e in out.items()}


CWNS = "https://www.hydroshare.org/resource/3dab07fd628a4af2ba812f038b1af89f/data/contents/2022"


@functools.lru_cache(None)
def cwns_design_flows():
    """Current design flow (MGD) of Michigan wastewater plants by NPDES permit, EPA Clean Watersheds Needs Survey 2022
    (HydroShare mirror, Hodson et al. 2026). CWNS has no actual flows."""
    import csv
    for f in ("FLOW", "FACILITY_PERMIT"):
        path = os.path.join(RAW, f"cwns2022_{f}.csv")
        if not os.path.exists(path):
            urllib.request.urlretrieve(f"{CWNS}/{f}.csv", path)
    total = {}
    for r in csv.DictReader(open(os.path.join(RAW, "cwns2022_FLOW.csv"))):
        if r["STATE_CODE"] == "MI" and r["FLOW_TYPE"] == "Total Flow" and r["CURRENT_DESIGN_FLOW"]:
            total[r["CWNS_ID"]] = float(r["CURRENT_DESIGN_FLOW"])
    out = {}
    for r in csv.DictReader(open(os.path.join(RAW, "cwns2022_FACILITY_PERMIT.csv"))):
        if r["STATE_CODE"] == "MI" and r["CWNS_ID"] in total and r["PERMIT_NUMBER"]:
            out[r["PERMIT_NUMBER"]] = total[r["CWNS_ID"]]
    return out


def plant_name(n):
    """'YCUA REGIONAL WWTP' -> 'YCUA Regional WWTP' (as on Water Ledger)."""
    up = {"WWTP", "WRRF", "WWTF", "WTF", "WWSL", "STP", "RTB", "RTF", "CSO", "GLWA", "YCUA", "SCI"}
    word = lambda w: w if w in up else ("County" if w == "CO" else w.capitalize())
    return re.sub(r"[A-Za-z]+", lambda m: word(m.group(0).upper()), str(n).lower())


def locate(lat, lon):
    """HUC12 and county containing a point (USGS WBD, Census TIGERweb)."""
    from waterledger_data import places as pl
    h = next((q for q in pl._layer_polys(6, "huc12,name", "wbd_huc12_mi.json")
              if q["bbox"][0] <= lon <= q["bbox"][2] and q["bbox"][1] <= lat <= q["bbox"][3] and pl._inside(lon, lat, q["rings"])), None)
    c = next((c for c in pl.counties() if pl._inside(lon, lat, c["rings"])), None)
    return {"huc12": h["huc12"] if h else None, "huc12_name": h["name"] if h else None,
            "county_fips": c["geoid"] if c else None, "county": c["name"] if c else None}


def downstream(huc12, hops=25):
    """The HUC12s the water passes through, starting with the site's own: [{code, name, listings, trout}]."""
    H, T = by_huc12(), trout_by_huc12()
    out, h = [], huc12
    while h and h in H and len(out) < hops:
        out.append({"code": h, "name": H[h]["n"], "listings": H[h].get("i", []), "trout": T.get(h), "assessed": bool(H[h].get("a"))})
        h = H[h]["t"]
    return out


def huc_name(n, cap=False):
    """In a sentence, 'Headwaters Little Rabbit River' -> 'the headwaters of the Little Rabbit River' (same rule as wq.js hucName)."""
    m = re.match(r"^Headwaters (.+)$", n or "")
    s = (f"the headwaters of {'the ' if re.search(r'River$', m.group(1)) else ''}{m.group(1)}" if m
         else f"the {n}" if n and re.search(r"River$", n) and "-" not in n else (n or ""))
    return s[:1].upper() + s[1:] if cap else s


def place_stem(name):
    """'Gaines Charter Township' / 'Gaylord city' -> 'gaines' / 'gaylord', to match a plant's city."""
    return re.sub(r"\s+(charter township|township|city)$", "", str(name).strip(), flags=re.I).lower()


def nearest_plants(lat, lon, k=3, km=40, stem=None):
    """Sewer plants for a place, as on Water Ledger: a plant in the place's own city or township first (any size), then the nearest
    plants of 0.5 MGD design or more within km."""
    import math
    rows = []
    for p in potws():
        d = 6371 * math.acos(min(1, math.sin(math.radians(lat)) * math.sin(math.radians(p["lat"])) +
                                 math.cos(math.radians(lat)) * math.cos(math.radians(p["lat"])) * math.cos(math.radians(p["lon"] - lon))))
        own = bool(stem) and p["city"].lower() == stem
        if (own and d <= km) or (d <= km and p["design_mgd"] >= 0.5):
            rows.append({**p, "km": round(d, 1), "own": own})
    return sorted(rows, key=lambda r: (not r["own"], r["km"]))[:k]


@functools.lru_cache(None)
def recode_aus():
    """USGS recoded some Michigan HUC12s after EGLE assigned assessment-unit IDs (e.g. the Huron River moved from 0409 to 0410).
    For units whose ID carries a code no longer in WBD, find the current HUC12 from the unit's own geometry (a middle vertex).
    Returns {assessment unit ID: current HUC12}."""
    def fetch():
        links = huc12_links()
        aus, _ = attains()
        stale = sorted(a for a in aus if re.match(r"MI(\d{12})", a) and re.match(r"MI(\d{12})", a).group(1) not in links)
        pts = {}
        for layer in (0, 1, 2):
            for i in range(0, len(stale), 100):
                ids = ",".join(f"'{a}'" for a in stale[i:i + 100])
                d = _get(f"{ATTAINS}/{layer}/query", {"where": f"assessmentunitidentifier IN ({ids})", "outFields": "assessmentunitidentifier",
                                                      "returnGeometry": "true", "outSR": 4326, "maxAllowableOffset": 0.002, "geometryPrecision": 4, "f": "json"})
                for f in d.get("features", []):
                    g = f.get("geometry") or {}
                    v = ([p for path in g.get("paths", []) for p in path] or [p for ring in g.get("rings", []) for p in ring]
                         or ([[g["x"], g["y"]]] if "x" in g else []))
                    if v:
                        if g.get("rings"):
                            v = [[sum(p[0] for p in v) / len(v), sum(p[1] for p in v) / len(v)]]
                        pts[f["attributes"]["assessmentunitidentifier"]] = v[len(v) // 2]
        return pts
    pts = _cached("attains_stale_au_points.json", fetch)
    from waterledger_data import places as pl
    polys = pl._layer_polys(6, "huc12,name", "wbd_huc12_mi.json")
    out = {}
    for au, (x, y) in pts.items():
        for q in polys:
            b = q["bbox"]
            if b[0] <= x <= b[2] and b[1] <= y <= b[3] and pl._inside(x, y, q["rings"]):
                out[au] = q["huc12"]
                break
    return out


WELLOGIC = "https://gisagoegle.state.mi.us/arcgis/rest/services/EGLE/DwOpenData/MapServer/3/query"


@functools.lru_cache(None)
def household_wells():
    """Household wells logged in EGLE's Wellogic by county and township: how many draw from glacial deposits (drift) vs bedrock,
    their average depth and static water level (ft). Returns {(county, township): {"drift": {...}, "rock": {...}}}."""
    from waterledger_data import places as pl

    def fetch():
        out = []
        for c in sorted({c["name"] for c in pl.counties()}):
            stats = [{"statisticType": "count", "onStatisticField": "OBJECTID", "outStatisticFieldName": "n"},
                     {"statisticType": "avg", "onStatisticField": "WELL_DEPTH", "outStatisticFieldName": "depth"},
                     {"statisticType": "avg", "onStatisticField": "SWL", "outStatisticFieldName": "swl"}]
            d = _get(WELLOGIC, {"where": f"COUNTY='{c}' AND WELL_TYPE='HOSHLD' AND AQ_TYPE IS NOT NULL", "outStatistics": json.dumps(stats),
                                "groupByFieldsForStatistics": "TOWNSHIP,AQ_TYPE", "f": "json"}, 300)
            out += [{"county": c, **f["attributes"]} for f in d.get("features", [])]
        return out
    out = {}
    for r in _cached("wellogic_household_by_township.json", fetch):
        if not r["TOWNSHIP"]:
            continue
        e = out.setdefault((r["county"], r["TOWNSHIP"].strip().lower()), {})
        e[r["AQ_TYPE"].lower()] = {"n": r["n"], "depth": round(r["depth"] or 0), "swl": round(r["swl"]) if r["swl"] else None}
    return out
