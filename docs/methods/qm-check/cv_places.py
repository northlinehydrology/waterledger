"""The station check's 21 places, corrected without their own station, through the cooling model.

Each place's cell is the land rule's. Its reference is the nearest qualifying station from the station check; that station, and any
other within 5 km of it, is taken out of the anchors before the place's cell is corrected (leave one station out). The corrected
cell runs through cooling.run_location as station_check.py does (model 1.7, 400 draws, seed 7, per 100 MW), and the results are
compared with the reference station's run there. Writes cv_places.json beside this file (runs of other ways kept).
Usage: python cv_places.py OUT [--shore] WAY [WAY ...]; --shore runs only the places whose cell is under 90% land."""
import json, os, sys
from concurrent.futures import ProcessPoolExecutor

import anchors as A
import qm
import cv_weather as W

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "era5-check"))
from station_check import pick                          # noqa: E402

ST, SCRATCH, ORO = None, None, None


def init(out):
    global ST, SCRATCH, ORO
    SCRATCH, ORO = A.setup(out)
    ST = A.load_anchors(out)


def one(job):
    r, way = job
    from waterledger_models.datacenter import cooling as cw
    from waterledger_models.datacenter.physics import design_dry_bulb
    ref = r["nearest_station"]
    rest = [a for a in ST if a["id"] != ref["id"] and qm.km(a["lat"], a["lon"], ref["lat"], ref["lon"]) > 5]
    cid, clat, clon, land = A.cell_of(r["lat"], r["lon"])
    et, ee, ed = A.era5(SCRATCH, cid)
    qe = qm.fit(et, ee, ed)
    target = {"lat": clat, "lon": clon, "qe": qe, "elev_m": A.elev(ORO, clat, clon)}
    d = qm.delta(target, rest, **W.WAYS[way])
    tc, tdc = (ee, ed) if d is None else qm.apply(et, ee, ed, qe, d)
    rh = qm.rh_from(tc, tdc)
    res = cw.run_location(list(et), tc, rh)
    used = [(a["name"], round(float(qm.km(clat, clon, a["lat"], a["lon"])), 1), round(float(w), 3)) for a, w in qm.weights(clat, clon, rest, **{k: v for k, v in W.WAYS[way].items() if k != "how"})]
    return {"geoid": r["geoid"], "way": way, "cell": cid, "cell_land": land, "corrected": d is not None, "anchors": used,
            **pick(res), "design_db": design_dry_bulb(tc), "rh_max": float(rh.max()), "td_over_t": int((tdc > tc + 1e-9).sum())}


if __name__ == "__main__":
    out, ways = sys.argv[1], [w for w in sys.argv[2:] if w != "--shore"]
    d = json.load(open(os.path.join(HERE, "..", "era5-check", "station_check_results.json")))
    rows = d["rows"]
    if "--shore" in sys.argv:
        A.setup(out)
        rows = [r for r in rows if A.cell_of(r["lat"], r["lon"])[3] < qm.SHORE_LAND]
    jobs = [(r, w) for w in ways for r in rows]
    with ProcessPoolExecutor(6, initializer=init, initargs=(out,)) as pool:
        got = list(pool.map(one, jobs))
    path = os.path.join(HERE, "cv_places.json")
    old = json.load(open(path))["runs"] if os.path.exists(path) else []
    keep = [x for x in old if (x["geoid"], x["way"]) not in {(r["geoid"], w) for r, w in jobs}]
    json.dump({"runs": keep + got}, open(path, "w"), indent=1, default=float)
    print("wrote cv_places.json,", len(got), "runs")
