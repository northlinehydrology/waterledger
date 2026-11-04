"""Count the nearest ERA5 (0.25 deg) and ERA5-Land (0.1 deg) grid cells for every place in the 2026-11-02.2 snapshots."""
import json
import numpy as np
from waterledger_data.config import CACHE
C = CACHE + "/snapshots"
def places(st):
    d = json.load(open(f"{C}/{st}/2026-11-02.2/places.json"))
    x = d["places"] if "places" in d else d
    rows = list(x.values()) if isinstance(x, dict) else x
    return rows
def hav(a, b, c, d):
    a, b, c, d = map(np.radians, (a, b, c, d))
    return 2 * 6371 * np.arcsin(np.sqrt(np.sin((c - a) / 2) ** 2 + np.cos(a) * np.cos(c) * np.sin((d - b) / 2) ** 2))
out = {}
allcells, allland = set(), set()
for st in ("MI", "OH", "VA", "TX"):
    rows = places(st)
    lat = np.array([float(r["lat"]) for r in rows]); lon = np.array([float(r["lon"]) for r in rows])
    levels = {}
    for r in rows:
        levels[r.get("level")] = levels.get(r.get("level"), 0) + 1
    ci, cj = np.round(lat / 0.25).astype(int), np.round(lon / 0.25).astype(int)
    li, lj = np.round(lat / 0.1).astype(int), np.round(lon / 0.1).astype(int)
    cells = set(zip(ci, cj)); land = set(zip(li, lj))
    dist = hav(lat, lon, ci * 0.25, cj * 0.25)
    allcells |= cells; allland |= land
    nonc = [r for r in rows if r.get("level") != "county"]
    ci2 = {(round(float(r["lat"]) / 0.25), round(float(r["lon"]) / 0.25)) for r in nonc}
    out[st] = {"places": len(rows), "levels": levels, "era5_cells": len(cells), "era5_cells_without_county_rows": len(ci2), "era5_land_cells": len(land),
               "km_to_cell_center_median": round(float(np.median(dist)), 1), "km_max": round(float(dist.max()), 1),
               "places_per_cell_max": int(max(np.unique(ci * 100000 + cj, return_counts=True)[1]))}
out["all"] = {"era5_cells": len(allcells), "era5_land_cells": len(allland)}
print(json.dumps(out, indent=1))
