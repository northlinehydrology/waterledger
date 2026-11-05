"""Places whose nearest ERA5 cell is mostly water (land-sea mask < 0.5), and where the nearest mostly-land cell is.
Usage: python water_cells.py DIR, with DIR/lsm/lsm.npz from lsm_fetch.py."""
import json, sys
import numpy as np
S = sys.argv[1]
z = np.load(S + "/lsm/lsm.npz"); lsm = z["lsm"]
def mask(ci, cj):                      # ci = lat*4, cj = lon*4 (lon negative)
    return float(lsm[360 - ci, (cj + 1440) % 1440])
from waterledger_data.config import CACHE
C = CACHE + "/snapshots"
out = {}
for st in ("MI", "OH", "VA", "TX"):
    x = json.load(open(f"{C}/{st}/2026-11-02.2/places.json"))["places"]
    rows = list(x.values()) if isinstance(x, dict) else x
    wet, cells, wetcells, lowland = [], set(), set(), 0
    for r in rows:
        lat, lon = float(r["lat"]), float(r["lon"])
        ci, cj = round(lat * 4), round(lon * 4)
        cells.add((ci, cj))
        m = mask(ci, cj)
        if m < 0.5:
            best = min(((ci + a - lat * 4) ** 2 + (cj + b - lon * 4) ** 2, (ci + a, cj + b)) for a in range(-4, 5) for b in range(-4, 5) if mask(ci + a, cj + b) >= 0.5)
            wet.append((r["name"], round(m, 2), best[1][0] / 4, best[1][1] / 4, round(111 * best[0] ** 0.5 / 4, 1))); wetcells.add((ci, cj))
        elif m < 0.9:
            lowland += 1
    land_rule = {(round(float(r["lat"]) * 4), round(float(r["lon"]) * 4)) for r in rows}
    out[st] = {"places": len(rows), "nearest_cell_mostly_water": len(wet), "water_cells": len(wetcells), "cells_0.5_to_0.9_land_places": lowland, "examples": wet[:8]}
print(json.dumps(out, indent=1))
