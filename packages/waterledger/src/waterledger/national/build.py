"""Build one state's national-tier data from the public sources, stage by stage, with timings: the work a snapshot job
does (design 0003). Each stage caches what it fetches or computes, so a stopped build resumes where it left off.

    waterledger build-state OH [--out DIR]
"""
import json, os, time

from waterledger import states

STAGES = ["places", "supply", "wastewater", "receiving", "climate", "energy", "wateruse", "checks"]
# The least share of a state's places each layer must cover; a build below these fails (a source may have broken).
# climate_division: a county NOAA's table leaves out (Poquoson, Virginia) uses the nearest division's station, so a sliver short
# of 100% is expected; a larger gap would mean the table or the county codes changed.
# county_water_use: USGS's 2015 counties; a county created since 2015 would have none.
COVERAGE_MIN = {"watersheds": 0.99, "utilities": 0.95, "climate_division": 0.99, "sewer_plant_within_40km": 0.5, "county_water_use": 0.99}
SAMPLE = 50


def checks(state, pl, sample=SAMPLE, seed=1):
    """Statewide checks: how much of the state each layer covers (failing below COVERAGE_MIN), and a random sample of places
    run through place.context() and site.estimate() for every cooling design, failing on any error."""
    import math

    import waterledger as wl
    from waterledger_data import divisions, energy, receiving, supply, wastewater, wateruse
    n = len(pl)
    plants = wastewater.plants(state)
    usgs = wateruse.usgs_2015(state)["counties"]

    def near_plant(lat, lon):
        for q in plants:
            dlat, dlon = math.radians(q["lat"] - lat), math.radians(q["lon"] - lon)
            h = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat)) * math.cos(math.radians(q["lat"])) * math.sin(dlon / 2) ** 2
            if 12742.0 * math.asin(math.sqrt(h)) <= 40:
                return True
        return False
    cd = divisions.county_divisions()
    cov = {"water_system": len(supply.systems_by_place(state, pl)) / n,
           "watersheds": sum(1 for v in receiving.watersheds_by_place(state, pl).values() if v["h12"]) / n,
           "utilities": len(energy.utilities_by_place(state, pl)) / n,
           "climate_division": sum(1 for f in pl.county_fips if f in cd) / n,
           "sewer_plant_within_40km": sum(near_plant(r.lat, r.lon) for r in pl.itertuples()) / n,
           "county_water_use": sum(1 for f in pl.county_fips if f in usgs) / n}
    cov = {k: round(v, 3) for k, v in cov.items()}
    low = {k: v for k, v in cov.items() if k in COVERAGE_MIN and v < COVERAGE_MIN[k]}
    errors = []
    for r in pl.sample(min(sample, n), random_state=seed).itertuples():
        try:
            p = wl.place(geoid=r.geoid)
            p.context()
            for cool in ("dry", "assist", "hybrid", "towers"):
                wl.Site(place=p, facility=wl.DataCenter(it_mw=100, cooling=cool)).estimate()
        except Exception as e:                       # noqa: BLE001  any failure is reported, with the place
            errors.append(f"{r.name} ({r.geoid}): {type(e).__name__}: {e}"[:300])
    result = {"coverage": cov, "sampled": min(sample, n), "errors": errors}
    if low or errors:
        raise RuntimeError(f"{state} checks failed: coverage below minimum {low}; {len(errors)} sample errors: {errors[:5]}")
    return result


def build(state, out=None, n=200, run_checks=True):
    """Run every stage for `state` and write a manifest of what was built (counts, timings, sources' dates) to `out`."""
    from waterledger.national import climate as nc
    from waterledger.national.data import LiveData
    from waterledger_data import energy, receiving, supply, wastewater, wateruse
    from waterledger_models import MODEL_VERSION
    state = state.upper()
    fips = next(f for f, s in states.FIPS.items() if s == state)
    report, t_all = {"state": state, "fips": fips, "model_version": MODEL_VERSION, "stages": {}}, time.time()

    def stage(name, fn):
        t = time.time()
        print(f"{state} {name} ...", flush=True)
        result = fn()
        report["stages"][name] = {"seconds": round(time.time() - t, 1), **result}
        print(f"{state} {name} done in {report['stages'][name]['seconds']} s: {result}", flush=True)

    pl = None

    def places():
        nonlocal pl
        pl = LiveData(state).places()
        return {"places": int(len(pl)), "by_level": {k: int(v) for k, v in pl.level.value_counts().items()}}
    stage("places", places)
    stage("supply", lambda: {"systems": int(len(supply.water_systems(state))), "places_served": len(supply.systems_by_place(state, pl))})
    stage("wastewater", lambda: {"plants": len(wastewater.plants(state))})
    stage("receiving", lambda: {"huc12": len(receiving.by_huc12(state)), "places_with_watersheds": len(receiving.watersheds_by_place(state, pl))})
    stage("climate", lambda: {"divisions": len(nc.division_runs(state, n)), "counties_with_storms": len(nc.storms_and_rain(state)[0])})
    stage("energy", lambda: {"places_with_utilities": len(energy.utilities_by_place(state, pl)), "utilities_with_loads": len(energy.loads(state))})

    def water_use():
        national, own = wateruse.usgs_2015(state), wateruse.state_layer(state)
        return {"usgs_counties": len(national["counties"]), "usgs_year": national["basis"]["year"],
                "state_source": own["basis"]["source"] if own else None, "state_year": own["basis"]["year"] if own else None,
                "state_counties": len(own["counties"]) if own else 0}
    stage("wateruse", water_use)
    if run_checks:
        stage("checks", lambda: checks(state, pl))
    report["seconds"] = round(time.time() - t_all, 1)
    if out:
        os.makedirs(out, exist_ok=True)
        json.dump(report, open(os.path.join(out, f"{state}_build.json"), "w"), indent=1)
    return report


def check_snapshot(state, root):
    """Run the statewide checks against a written snapshot (root/<ST>/<date>/) instead of the live services, and record the
    results in its manifest. Much faster than checking live: the downstream paths are already in the snapshot."""
    import os

    from waterledger.national import data
    state = state.upper()
    date = sorted(os.listdir(os.path.join(root, state)))[-1]
    folder = os.path.join(root, state, date)
    os.environ["WATERLEDGER_DATA_URL"] = "file://" + os.path.abspath(root)
    os.environ["WATERLEDGER_DATA_DATE"] = date
    data.state_data.cache_clear()
    sd = data.state_data(state)
    result = checks(state, sd.places())
    m = json.load(open(os.path.join(folder, "manifest.json")))
    m["checks"] = result
    json.dump(m, open(os.path.join(folder, "manifest.json"), "w"), separators=(",", ":"))
    print(f"{state} snapshot {date} checks: {result}")
    return result
