"""Michigan's provider: answers for Michigan places from Water Ledger Michigan's data files (the same ones waterledger.org/mi
reads), through waterledger.scenario, so the package and the page agree."""
from waterledger import scenario as sc
from waterledger.national.provider import water_use_record

# EGLE's groups on waterledger.org/mi -> the county water-use categories (waterledger_data.wateruse.CATEGORIES)
EGLE_CATS = {"Public water systems": "public_supply", "Industry": "industrial", "Bottled water": "industrial", "Farm irrigation": "irrigation",
             "Golf courses": "golf", "Livestock": "livestock", "Mining and dewatering": "mining", "Power plants": "thermoelectric", "Other": "other"}


def find(name, county=None):
    return sc.find(name, county)


def place(geoid):
    from waterledger.place import Place
    r = sc.place(geoid)
    lon, lat = sc.lonlat(r)
    return Place(geoid=r["g"], name=r["base"], kind=r["k"], state="MI", county=r["c"], county_fips=r["cf"], lat=round(lat, 4), lon=round(lon, 4))


def estimate(site):
    """Water use for a site at a Michigan place, through waterledger.scenario (the page's est())."""
    from waterledger.estimate import Electricity, Estimate, Flow, Range, WaterUse
    f = site.facility
    S = sc.scenario(site.place.geoid, mw=f.it_mw, cool=f.cooling, src=site.source, dest=site.wastewater, acres=site.acres,
                    before=site.land_before, imp=site.impervious)
    E, R = S["E"], Range.from_band
    water = WaterUse(withdrawn=Flow(avg=R(E["wAvg"]), peak_day=R(E["wPeak"])), withdrawn_annual_mg=R(E["wAnn"]),
                     consumed=Flow(avg=R(E["cAvg"]), peak_day=R(E["cPeak"])), returned=Flow(avg=R(E["rAvg"]), peak_day=R(E["rPeak"])),
                     to_sewer=R(E["sewer"]), lake_source=E["lake"], reuse=E["reuse"])
    resolved = site.model_copy(update={"source": S["src"], "wastewater": S["dest"], "acres": S["acres"], "land_before": S["before"]})
    D = sc.data("estimates")
    e = sc.electricity(D, S["place"]["r"], f.cooling, f.it_mw)
    power = Electricity(avg_mw=R(e["mw"]), peak_mw=R(e["peak_mw"]), pue=R(e["pue"]), peak_pue=R(e["peak_pue"])) if e else None
    return Estimate(site=resolved, water=water, electricity=power, model_version=D["model_version"], data_date=D["generated"])


def context(place):
    """Michigan's context for a place: every category from Water Ledger Michigan's data (EGLE, EPA, USGS, NOAA, MPSC, EIA)."""
    from waterledger import context as cx
    r, E, Wd, P = sc.place(place.geoid), sc.data("estimates"), sc.data("waters"), sc.data("power")
    sys_ = lambda w: cx.WaterSystem(pwsid=w["pwsid"], name=w["name"].title(), population=w.get("pop"), connections=w.get("connections"), share_of_place=w.get("share"))
    near = None if r["w"] else sc.near_system(r)
    wells = Wd["wells"].get(r["g"])
    L = egle_layer()
    egle = L["counties"].get(r["cf"])
    supply = cx.Supply(provider="MI", sources=["epa_sa", "egle2025", "wellogic"], systems=[sys_(w) for w in r["w"]],
                       nearest_system=sys_(near["w"]) if near else None, nearest_system_km=round(near["km"], 1) if near else None,
                       county_use_mgd=E["county_uses_mgd"].get(r["c"], {}),
                       county_water_use=water_use_record(egle, L["basis"], r["cf"]) if egle else None,
                       household_wells=dict(zip(("drift_n", "drift_depth_ft", "drift_level_ft", "rock_n", "rock_depth_ft", "rock_level_ft"), wells)) if wells else None)
    plants = [cx.SewerPlant(npdes=q["id"], name=q["n"], design_mgd=q.get("design"), flow_mgd=q.get("flow"), km=round(q["km"], 1),
                            receiving_water=q.get("recv") or None, combined_sewer=bool(q.get("cso")), lagoon=bool(q.get("lagoon")))
              for q in sc._plants_near(r)]
    G = Wd["groups"]
    path, h = [], (r["h12"][0]["code"] if r["h12"] else None)
    while h and h in Wd["h12"] and len(path) < 25:
        x = Wd["h12"][h]
        path.append(cx.Reach(huc12=h, name=x["n"], impairments=[G[i[0]] for i in x.get("i", [])], tmdl=[G[i[0]] for i in x.get("i", []) if i[1]],
                             coldwater_streams=x["tr"][1] if x.get("tr") else []))
        h = x["t"]
    receiving = cx.Receiving(provider="MI", sources=["usgs_wbd", "attains2026", "mdnr_trout"],
                             watersheds=[cx.Watershed(huc12=w["code"], name=w["name"], share_of_place=w.get("share")) for w in r["h12"]],
                             basin=cx.Watershed(huc12=r["h8"]["code"], name=r["h8"]["name"]) if r.get("h8") else None,
                             great_lake=(r.get("gl") or {}).get("lake"), downstream=path)
    meta = E["region_meta"][r["r"]]
    climate = cx.Climate(provider="MI", sources=["era5", "noaa_cag", "noaa_atlas14"], region=r["r"], region_name=meta["name"], station=meta["station"],
                         rain_in=Wd["rain_in"].get(r["cf"]), design_storms_in=E["county_storms_in"].get(r["cf"], {}))
    U = P["utilities"]
    from waterledger.national.provider import _ppw
    energy = cx.Energy(provider="MI", sources=["mpsc_territory", "eia861", "eia923_2024", "macknick2012"], power_plant_water=_ppw("MI"),
                       utilities=[cx.Utility(name=U[i]["n"], type=U[i]["type"], share_of_place=sh, customers=U[i].get("cust"),
                                             avg_mw=U[i].get("avg_mw"), summer_peak_mw=U[i].get("summer_mw")) for i, sh in P["places"].get(r["g"], [])])
    jur = cx.Jurisdiction(provider="MI", sources=["census_tiger"], name=place.name, kind=place.kind, county=place.county, state="MI")
    return cx.Context(place=place, jurisdiction=jur, supply=supply, wastewater=cx.Wastewater(provider="MI", sources=["echo", "cwns2022"], plants=plants),
                      receiving=receiving, climate=climate, energy=energy)


def place_at(lat, lon):
    """Michigan places are its county subdivisions (cities and townships), so a point maps to the subdivision containing it."""
    from waterledger_data.census import LAYERS
    from waterledger_data.places import _get
    d = _get(LAYERS["cousub"], {"geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint", "inSR": 4326,
                                "spatialRel": "esriSpatialRelIntersects", "outFields": "GEOID", "returnGeometry": "false", "f": "json"})
    f = d.get("features", [])
    return f[0]["attributes"]["GEOID"] if f else None


def egle_layer():
    """EGLE's reported withdrawals by county as a water-use layer (waterledger_data.wateruse's shape), from the numbers
    waterledger.org/mi shows (estimates.json county_uses_mgd); EGLE's own groups are kept in source_values."""
    from waterledger_data.wateruse import CATEGORIES
    E = sc.data("estimates")
    fips = {p["c"]: p["cf"] for p in sc.data("places")["places"]}
    src = E["sources"]["egle2025"]
    out = {}
    for county, groups in E["county_uses_mgd"].items():
        if county not in fips:
            continue
        mgd = {}
        for g, v in groups.items():
            c = EGLE_CATS.get(g, "other")
            mgd[c] = mgd.get(c, 0.0) + v
        mgd = {c: round(mgd[c], 3) for c in CATEGORIES if c in mgd}
        mgd["total"] = round(sum(mgd.values()), 3)
        out[fips[county]] = {"name": f"{county} County", "mgd": mgd, "source_values": groups}
    basis = {"source": "egle2025", "kind": "reported", "measure": "withdrawals", "year": 2025, "units": "Mgal/d", "source_units": "gallons per year",
             "citation": src["citation"], "url": src["url"],
             "threshold": "facilities able to withdraw 100,000 gallons a day or more (Part 327, NREPA) report each year",
             "categories": {v: k for k, v in EGLE_CATS.items() if k != "Bottled water"} | {"industrial": "Industry, and bottled water"},
             "caveats": ["Golf courses are irrigation facilities whose names mark them as golf or country clubs",
                         "Entries far outside the range of their kind are left out as likely reporting errors (see the methods page)",
                         "Gallons a year averaged over 365 days"]}
    return {"basis": basis, "counties": dict(sorted(out.items()))}
