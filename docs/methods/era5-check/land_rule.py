"""Every place's ERA5 cell under the land rule decided Nov 3, 2026: the nearest 0.25-degree cell, or, when its land-sea
mask is under 0.5, the nearest cell (great-circle distance from the place's internal point) whose mask is at least 0.5.
Writes cell_assignment.csv beside this file and prints counts. Usage: python land_rule.py DIR, with DIR/lsm/lsm.npz from lsm_fetch.py."""
import csv, json, math, os, sys
import numpy as np
from waterledger_data.config import CACHE

HERE = os.path.dirname(os.path.abspath(__file__))
SNAP = os.path.join(CACHE, "snapshots")
LAND = 0.5
lsm = None


def load(scratch):
    global lsm
    lsm = np.load(os.path.join(scratch, "lsm", "lsm.npz"))["lsm"]


def land(ci, cj):                                     # ci = lat * 4, cj = lon * 4 (lon negative)
    return float(lsm[360 - ci, (cj + 1440) % 1440])


def km(a, b, c, d):
    p = math.pi / 180
    h = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(h))


def nearest_land(lat, lon, need=LAND):
    """Search rings of cells outward; a ring k cells out is at least k x 27.8 km x cos(lat) away, so stop once that
    passes the best found. Ties go to the lower latitude, then the lower longitude, so the result is deterministic."""
    ci0, cj0 = round(lat * 4), round(lon * 4)
    best = None
    for k in range(1, 40):
        for a in range(-k, k + 1):
            for b in range(-k, k + 1):
                if max(abs(a), abs(b)) != k or land(ci0 + a, cj0 + b) < need:
                    continue
                c = (km(lat, lon, (ci0 + a) / 4, (cj0 + b) / 4), ci0 + a, cj0 + b)
                best = min(best, c) if best else c
        if best and best[0] < (k - 0.5) * 27.8 * math.cos(math.radians(lat + 1)):
            break
    return best[1], best[2]


cid = lambda ci, cj: f"{ci / 4:.2f}_{cj / 4:.2f}"


def main():
    load(sys.argv[1])
    rows, summary = [], {}
    for st in ("MI", "OH", "VA", "TX"):
        x = json.load(open(f"{SNAP}/{st}/2026-11-02.2/places.json"))["places"]
        places = list(x.values()) if isinstance(x, dict) else x
        s = {"places": len(places), "moved": 0, "cells_nearest": set(), "cells": set(), "moved_km_max": 0.0}
        for p in places:
            lat, lon = float(p["lat"]), float(p["lon"])
            ni, nj = round(lat * 4), round(lon * 4)
            moved = land(ni, nj) < LAND
            ci, cj = nearest_land(lat, lon) if moved else (ni, nj)
            r = {"state": st, "geoid": p["geoid"], "name": p["name"], "level": p.get("level"), "lat": lat, "lon": lon,
                 "nearest_cell": cid(ni, nj), "nearest_km": round(km(lat, lon, ni / 4, nj / 4), 1), "nearest_land": round(land(ni, nj), 3),
                 "cell": cid(ci, cj), "cell_km": round(km(lat, lon, ci / 4, cj / 4), 1), "cell_land": round(land(ci, cj), 3), "moved": int(moved)}
            rows.append(r)
            s["moved"] += moved
            s["cells_nearest"].add(r["nearest_cell"]); s["cells"].add(r["cell"])
            s["moved_km_max"] = max(s["moved_km_max"], r["cell_km"] if moved else 0)
        summary[st] = s
    with open(os.path.join(HERE, "cell_assignment.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    allc = set().union(*(s["cells"] for s in summary.values())); alln = set().union(*(s["cells_nearest"] for s in summary.values()))
    for st, s in summary.items():
        mk = [r["cell_km"] for r in rows if r["state"] == st and r["moved"]]
        print(st, s["places"], "places,", s["moved"], "moved,", len(s["cells_nearest"]), "->", len(s["cells"]), "cells; moved km median",
              round(float(np.median(mk)), 1) if mk else "-", "max", s["moved_km_max"])
    print("all", len(alln), "->", len(allc), "cells")


if __name__ == "__main__":
    main()
