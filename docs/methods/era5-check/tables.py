"""The markdown tables in era5-station-check.md, from station_check_results.json and the land-sea mask. Usage: python tables.py DIR (DIR/lsm/lsm.npz)."""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(HERE, "station_check_results.json")))
lsm = np.load(os.path.join(sys.argv[1], "lsm", "lsm.npz"))["lsm"]
land = lambda c: float(lsm[360 - round(c["lat"] * 4), (round(c["lon"] * 4) + 1440) % 1440])
short = lambda s: s.replace(" International Airport", " Intl").replace(" International Ap", " Intl").replace(" Regional Airport", "").replace(" Airport", "").replace(" area", " region point")
pct = lambda a, b: f"{100 * (a / b - 1):+.0f}%"
print("| Place | Published point (km) | Nearest qualifying station (km) | ERA5 cell (km, land share) |")
print("|---|---|---|---|")
for r in d["rows"]:
    p, n, c = r["published"], r["nearest_station"], r["era5_cell"]
    same = r["nearest"] is None
    print(f'| {r["name"]}, {r["state"]} | {short(p["point"])} ({p["km"]:.0f}) | {"same" if same else short(n["name"]) + " (" + format(n["km"], ".0f") + ")"} | {c["lat"]:.2f}, {c["lon"]:.2f} ({c["km"]:.0f} km, {land(c):.2f}) |')
for stat, title in (("withdrawn_avg", "average day"), ("withdrawn_peak_1in10", "1-in-10 peak day")):
    print(f"\n#### Cooling withdrawal, {title}, MGD per 100 MW (p50): published / nearest station / ERA5\n")
    print("| Place | Towers | ERA5 vs station | Hybrid | ERA5 vs station | Assist | ERA5 vs station |")
    print("|---|---|---|---|---|---|---|")
    for r in d["rows"]:
        p, e = r["published"], r["era5"]
        n = r["nearest"] or p
        cells = []
        for des in ("towers", "hybrid", "assist"):
            k = f"{des}.{stat}"
            cells += [f"{p[k]:.3f} / {n[k]:.3f} / {e[k]:.3f}", pct(e[k], n[k])]
        print(f'| {r["name"]} | ' + " | ".join(cells) + " |")
print("\n| Place | Design dry-bulb, station (C) | ERA5 (C) |")
print("|---|---|---|")
for r in d["rows"]:
    if r["nearest"]:
        print(f'| {r["name"]} | {r["nearest"]["design_db"]:.1f} | {r["era5"]["design_db"]:.1f} |')
