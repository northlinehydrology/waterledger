"""Michigan electric utilities: who serves each place and how big each utility's load is, cached under engine/data/raw/power/.

Sources (all public):
  MPSC     Electric Utility Service Areas (Michigan Public Service Commission GIS hub): the territory of every investor-owned,
           cooperative and municipal utility in Michigan, via ArcGIS REST
  EIA-861  Annual Electric Power Industry Report: each utility's Michigan retail sales and customers (bundled plus
           delivery-only; short-form filers included) and summer and winter peak demand (Operational Data)

A place's utilities are the MPSC territories covering its sampled area, with the share each covers. The utility's size is
its own customers' load, not where its power is generated: Michigan's utilities buy and sell through the MISO market.
"""
import glob, io, json, os, urllib.request, zipfile

from waterledger_data import places as pl
from waterledger_data.config import CACHE

RAW = os.path.join(CACHE, "power")
MPSC = "https://services3.arcgis.com/943LBv9FP414WfDO/arcgis/rest/services/ELECTRIC_UTILITY_SERVICE_AREA_MI_WFL1/FeatureServer/16/query"
EIA861 = "https://www.eia.gov/electricity/data/eia861/zip/f861{year}.zip"

# MPSC territory name -> EIA utility number (checked by hand against names and customer counts, Oct 2026)
EIA_ID = {
    "DTE Electric Company": 5109, "Consumers Energy Company": 4254, "Indiana Michigan Power Company": 9324, "Upper Peninsula Power Company": 19578,
    "Upper Michigan Energy Resources Corporation": 60631, "Alpena Power Company": 392, "Northern States Power Company - Wisconsin": 13780,
    "Great Lakes Energy Cooperative": 38084, "Cloverland Electric Cooperative": 3828, "Cherryland Electric Cooperative": 3436,
    "Midwest Energy Cooperative": 12377, "Presque Isle Electric & Gas Cooperative": 15340, "Homeworks Tri-County Electric Cooperative": 19396,
    "Thumb Electric Cooperative": 18895, "Alger Delta Cooperative Electric Association": 305, "Ontonagon County Rural Electrification Association": 14156,
    "Bayfield Electric Cooperative": 1367, "Lansing Board of Water & Light": 10704, "Holland Board of Public Works": 8723,
    "Bay City Electric Light & Power": 1366, "Marquette Board of Light and Power": 11701, "Grand Haven Board of Light & Power": 7483,
    "Traverse City Light & Power": 19125, "Wyandotte Municipal Services": 21048, "City of South Haven": 17562, "City of Niles": 13604,
    "Coldwater Board of Public Utilities": 3915, "City of Escanaba": 24558, "City of Sturgis": 18252, "Zeeland Board of Public Works": 21158,
    "Hillsdale Board of Public Utilities": 8631, "City of Petoskey": 14867, "City of Marshall": 11713, "City of Charlevoix": 3384,
    "City of Harbor Springs": 8083, "City of Chelsea": 3415, "City of Eaton Rapids": 5630, "Lowell Light & Power": 11268, "City of Dowagiac": 5343,
    "City of Gladstone": 7265, "City of Portland": 15246, "City of Negaunee": 13352, "City of Norway": 13826, "City of St Louis": 17886,
    "Village of Paw Paw": 14581, "City of Crystal Falls": 4604, "Village of Union City": 19432, "Village of Clinton": 3813,
    "Village of Newberry": 13525, "City of Hart": 8205, "Sebewaing Light & Water": 16873, "City of Croswell": 4562, "Village of L'Anse": 10508,
    "City of Wakefield": 19975, "Village of Baraga": 1196, "City of Stephenson": 18074, "Village of Daggett": 4792,
}


def _cached(name, fn):
    path = os.path.join(RAW, name)
    if not os.path.exists(path):
        os.makedirs(RAW, exist_ok=True)
        json.dump(fn(), open(path, "w"))
    return json.load(open(path))


def territories():
    """MPSC service territories with generalized polygons."""
    def fetch():
        out, off = [], 0
        while True:
            d = pl._get(MPSC, {"where": "1=1", "outFields": "Name,Type,Customers,Counties_1", "returnGeometry": "true", "outSR": 4326,
                               "maxAllowableOffset": 0.002, "geometryPrecision": 4, "resultOffset": off, "resultRecordCount": 100, "f": "json"})
            for f in d.get("features", []):
                a = f["attributes"]
                out.append({"name": a["Name"].strip(), "type": a["Type"], "customers": a["Customers"], "counties": a["Counties_1"],
                            "rings": (f.get("geometry") or {}).get("rings") or []})
            if len(d.get("features", [])) < 100:
                return out
            off += 100
    polys = _cached("mpsc_service_areas.json", fetch)
    for q in polys:
        xs = [p[0] for r in q["rings"] for p in r] or [0]
        ys = [p[1] for r in q["rings"] for p in r] or [0]
        q["bbox"] = (min(xs), min(ys), max(xs), max(ys))
    return polys


def eia_year():
    """The newest EIA-861 year on disk."""
    have = sorted(glob.glob(os.path.join(RAW, "eia861_[0-9][0-9][0-9][0-9]")))
    if not have:
        raise FileNotFoundError("No EIA-861 data in " + RAW + "; run `python -m engine.update --only eia861`")
    return int(have[-1][-4:])


def fetch_eia861(year):
    """Download and unpack one year of EIA-861 (about 5 MB). EIA posts a year's final data the following fall."""
    with urllib.request.urlopen(EIA861.format(year=year), timeout=300) as r:
        z = zipfile.ZipFile(io.BytesIO(r.read()))
    d = os.path.join(RAW, f"eia861_{year}")
    os.makedirs(d, exist_ok=True)
    for n in z.namelist():
        if n.startswith(("Sales_Ult_Cust_", "Short_Form_", "Operational_Data_", "Utility_Data_")):
            open(os.path.join(d, os.path.basename(n)), "wb").write(z.read(n))
    return d


def utility_loads(year=None, state="MI"):
    """{EIA id: {"mwh", "customers", "summer_mw", "winter_mw"}} for one state (Michigan by default). Sales are bundled plus delivery-only
    customers (everyone on the utility's wires); short-form filers report sales only. Peaks are as reported for the state (a multistate
    utility's peak in another state is absent)."""
    import pandas as pd
    year = year or eia_year()
    d = os.path.join(RAW, f"eia861_{year}")
    s = pd.read_excel(os.path.join(d, f"Sales_Ult_Cust_{year}.xlsx"), header=None, skiprows=3).iloc[:, [1, 3, 6, -2, -1]]
    s.columns = ["id", "part", "state", "mwh", "cust"]
    num = lambda col: pd.to_numeric(col, errors="coerce")      # EIA marks withheld or missing values with '.' or '..'
    s["mwh"], s["cust"] = num(s.mwh), num(s.cust)
    s = s[(s.state == state) & s.part.isin(["A", "C"])].groupby("id")[["mwh", "cust"]].sum()
    f = pd.read_excel(os.path.join(d, f"Short_Form_{year}.xlsx"))
    f = f[f["State"] == state].set_index("Utility Number")[["Total Sales (MWh)", "Total Customers"]]
    f.columns = ["mwh", "cust"]
    f["mwh"], f["cust"] = num(f.mwh), num(f.cust)
    o = pd.read_excel(os.path.join(d, f"Operational_Data_{year}.xlsx"), header=None, skiprows=3).iloc[:, [1, 3, 6, 7]]
    o.columns = ["id", "state", "summer", "winter"]
    o["summer"], o["winter"] = num(o.summer), num(o.winter)
    o = o[o.state == state].set_index("id")
    val = lambda v: float(v) if v == v and v is not None else None
    out = {}
    for uid, r in pd.concat([s, f]).iterrows():
        if r.mwh != r.mwh:
            continue
        pk = o.loc[uid] if uid in o.index else None
        out[int(uid)] = {"mwh": float(r.mwh), "customers": int(r.cust) if r.cust == r.cust else None,
                         "summer_mw": val(pk.summer) if pk is not None else None, "winter_mw": val(pk.winter) if pk is not None else None}
    return out


# EIA-861 Utility Data, "Operating in these RTOs" -> the grid-water table's balancing authority codes
RTO_BA = {"ERCOT": "ERCO", "PJM": "PJM", "MISO": "MISO", "SPP": "SWPP", "NYISO": "NYIS", "ISONE": "ISNE", "CAISO": "CISO"}


def utility_rtos(year=None):
    """{EIA utility id: balancing authority code} for utilities EIA-861 lists in exactly one RTO (Utility Data, "Operating in these
    RTOs"). Used where the service-territory layer gives no control area (e.g. Texas delivery companies listed as NOT AVAILABLE)."""
    import pandas as pd
    year = year or latest_eia861() or eia_year()
    path = os.path.join(RAW, f"eia861_{year}", f"Utility_Data_{year}.xlsx")
    if not os.path.exists(path):
        fetch_eia861(year)
    u = pd.read_excel(path, header=1).rename(columns={"SPP.1": "SPP"})
    out = {}
    for _, r in u.iterrows():
        flags = [RTO_BA[c] for c in RTO_BA if c in u.columns and str(r[c]).strip().upper() == "Y"]
        if len(set(flags)) == 1 and r["Utility Number"] == r["Utility Number"]:
            out[int(r["Utility Number"])] = flags[0]
    return out


def latest_eia861(download=True):
    """The newest EIA-861 year on disk; with none on disk, the newest year EIA has posted (downloaded), or None."""
    import datetime
    try:
        return eia_year()
    except FileNotFoundError:
        if not download:
            return None
    for y in range(datetime.date.today().year - 1, datetime.date.today().year - 4, -1):
        try:
            fetch_eia861(y)
            return y
        except Exception:                           # noqa: BLE001  not posted yet: try the year before
            continue
    return None


# EIA-861 Sales to Ultimate Customers: a state's totals sum Parts A (bundled), B (energy only) and D (bundled, Texas retail
# providers) for sales and customers; Part C (delivery only) repeats Part B's customers on the wires (EIA's note in the file).
STATE_PARTS = ("A", "B", "D")


def _sales(year):
    import pandas as pd
    s = pd.read_excel(os.path.join(RAW, f"eia861_{year}", f"Sales_Ult_Cust_{year}.xlsx"), header=None, skiprows=3).iloc[:, [3, 6, 7, 10, 11, -2]]
    s.columns = ["part", "state", "ownership", "res_mwh", "res_cust", "mwh"]
    for c in ("res_mwh", "res_cust", "mwh"):
        s[c] = pd.to_numeric(s[c], errors="coerce")
    return s


def state_retail_mwh(state, year=None):
    """All retail electricity sold in a state in a year (bundled and energy-only sales; EIA-861 Parts A, B and D), MWh."""
    year = year or eia_year()
    s = _sales(year)
    return float(s[(s.state == state) & s.part.isin(STATE_PARTS)].mwh.sum())


def michigan_retail_mwh(year=None):
    """All retail electricity sold in Michigan in a year: bundled sales plus energy-only (retail choice) sales, MWh."""
    return state_retail_mwh("MI", year)


def residential(state, year=None):
    """A state's residential customers and their average use: {"customers", "mwh", "kwh_month"} (EIA-861 Parts A, B and D;
    customers of 'Behind the Meter' respondents, third-party rooftop solar owners, left out as EIA does)."""
    year = year or eia_year()
    s = _sales(year)
    s = s[(s.state == state) & s.part.isin(STATE_PARTS)]
    mwh, cust = float(s.res_mwh.sum()), float(s[s.ownership != "Behind the Meter"].res_cust.sum())
    return {"customers": int(cust), "mwh": round(mwh), "kwh_month": round(mwh * 1000 / cust / 12, 1) if cust else None}


def place_utilities(rings, polys):
    """Utilities whose MPSC territory covers the place, with the share of its sampled area each covers (5% or more)."""
    return [(round(sh, 2), q["name"]) for sh, q in pl._local_shares(rings, [q for q in polys if q["rings"]])]
