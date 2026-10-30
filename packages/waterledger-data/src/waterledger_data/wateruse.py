"""Water use by county: the USGS 2015 estimates for every state. Cached under <cache>/wateruse/. Sources, structure
and caveats are in the methods note docs/methods/water-use-sources.md.

Every layer returns the same shape:

    {"basis": {source, citation, url, year, kind ("estimate" or "reported"), measure ("withdrawals" or "use"), units
               ("Mgal/d"), source_units, threshold, categories (what each category holds in the source), caveats},
     "counties": {county FIPS: {"name", "mgd": {category: Mgal/d}, "ground_mgd": {...}, "surface_mgd": {...},
                                "reuse_mgd": {...} (Texas), "delivered_to_homes_mgd" (USGS), "source_values": {the source's
                                own categories, in its own units}}}}

Categories are a small fixed set (CATEGORIES); a category is left out where the source has no value for it, rather than
written as zero. "total" is the sum of the categories present.

    usgs_2015(state=None)   USGS revised 2015 county estimates (Sleckman, Ross and Cook 2026), any state
"""
import calendar, json, os, urllib.request, zipfile

from waterledger_data.config import CACHE

RAW = os.path.join(CACHE, "wateruse")
CATEGORIES = ("public_supply", "domestic", "commercial", "industrial", "irrigation", "golf", "livestock", "aquaculture", "mining",
              "thermoelectric", "other", "total")
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
