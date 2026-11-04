"""How many cells and places the decided rule corrects in the four states, station set by station set: the cells under 90% land with
a shore station (its own cell under 90% land) within 100 km, against the Nov 4 proposal (any station within 100 km). Station sets are
cumulative: ISD under one ID, then ISD linked across ID changes, then ECCC. Writes coverage.json beside this file.
Usage: python coverage.py OUT"""
import csv, json, os, sys
from collections import defaultdict

import anchors as A
import qm

HERE = os.path.dirname(os.path.abspath(__file__))
SETS = [("isd", ("isd",)), ("+ linked", ("isd", "isd-linked")), ("+ eccc", ("isd", "isd-linked", "eccc"))]

if __name__ == "__main__":
    out = sys.argv[1]
    A.setup(out)
    st = [s for s in json.load(open(os.path.join(out, "stations.json"))) if s.get("qualifies")]
    for s in st:
        s["cell"], _, _, s["cell_land"] = A.cell_of(s["lat"], s["lon"])
    cells = defaultdict(lambda: {"places": 0, "by_state": defaultdict(int)})
    for r in csv.DictReader(open(os.path.join(HERE, "..", "era5-check", "cell_assignment.csv"))):
        c = cells[r["cell"]]
        c["places"] += 1
        c["by_state"][r["state"]] += 1
        c["land"] = float(r["cell_land"])
    shore = {k: v for k, v in cells.items() if v["land"] < qm.SHORE_LAND}
    res = {"cells": len(cells), "shore_cells": len(shore), "shore_places": sum(v["places"] for v in shore.values()),
           "shore_places_by_state": {stt: sum(v["by_state"].get(stt, 0) for v in shore.values()) for stt in ("MI", "OH", "VA", "TX")}, "sets": []}
    for name, src in SETS:
        use = [s for s in st if s.get("source", "isd") in src]
        row = {"set": name, "stations": len(use), "shore_stations": sum(s["cell_land"] < qm.SHORE_LAND for s in use)}
        for rule, shore_only in (("any", False), ("shore", True)):
            n, places, by_state = 0, 0, defaultdict(int)
            for k, v in shore.items():
                lat, lon = (float(x) for x in k.split("_"))
                if qm.weights(lat, lon, use, shore_only=shore_only):
                    n += 1
                    places += v["places"]
                    for stt, c in v["by_state"].items():
                        by_state[stt] += c
            row[rule] = {"cells": n, "places": places, "places_by_state": dict(by_state)}
        res["sets"].append(row)
    json.dump(res, open(os.path.join(HERE, "coverage.json"), "w"), indent=1)
    print(json.dumps(res))
