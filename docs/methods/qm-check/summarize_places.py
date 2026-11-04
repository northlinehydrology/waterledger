"""Tables of cv_places.json against the station check's reference stations: percent difference from the station, p50 per 100 MW.
"none" is the land rule's cell uncorrected (station_check_results.json; Lorain from land_rule_results.json); "shore" is the lapse
correction on cells under 90% land and none elsewhere (the Nov 4 proposal); "decided" is the rule decided Nov 4, 2026: lapse from shore
stations only, ISD, linked ISD and ECCC, on cells under 90% land ("shore_isd" and "shore_linked" are the same with fewer station sets)."""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
E = os.path.join(HERE, "..", "era5-check")
sc = json.load(open(os.path.join(E, "station_check_results.json")))["rows"]
lr = {r["geoid"]: r for r in json.load(open(os.path.join(E, "land_rule_results.json")))["rows"]}
runs = {(x["geoid"], x["way"]): x for x in json.load(open(os.path.join(HERE, "cv_places.json")))["runs"]}
SHORE = ["3944856", "5182000", "3916000", "2614765820", "3977000"]
STATS = [(d, s) for d in ("towers", "hybrid", "assist") for s in ("withdrawn_avg", "withdrawn_peak_1in10")]
WAYS = ["none", "bias", "lapse", "shore", "shore_isd", "shore_linked", "decided"]
NEW = {"shore_isd": "lapse_shore_isd", "shore_linked": "lapse_shore_linked", "decided": "lapse_shore"}
rows = []
for r in sc:
    ref = r["nearest"] or r["published"]
    none = lr[r["geoid"]]["era5"]["rule"] if r["geoid"] in lr else r["era5"]
    v = {"none": none, "bias": runs[(r["geoid"], "bias")], "lapse": runs[(r["geoid"], "lapse")]}
    land = runs[(r["geoid"], "lapse")]["cell_land"]
    v["shore"] = v["lapse"] if land < 0.9 else none
    for w, run in NEW.items():
        v[w] = runs[(r["geoid"], run)] if land < 0.9 else none
    err = {w: {f"{d}.{s}": 100 * (v[w][f"{d}.{s}"] / ref[f"{d}.{s}"] - 1) for d, s in STATS} for w in WAYS}
    for w in WAYS:
        err[w]["design_db"] = v[w]["design_db"] - ref["design_db"] if "design_db" in ref else None
    rows.append({"name": r["name"], "state": r["state"], "geoid": r["geoid"], "land": land, "err": err,
                 "corrected": runs[(r["geoid"], "lapse")]["corrected"], "anchors": runs[(r["geoid"], "lapse")]["anchors"],
                 "decided_corrected": land < 0.9 and v["decided"]["corrected"], "decided_anchors": v["decided"].get("anchors", []) if land < 0.9 else [],
                 "station": r["nearest_station"]["name"], "station_km": r["nearest_station"]["km"]})
json.dump(rows, open(os.path.join(HERE, "cv_places_summary.json"), "w"), indent=1)

label = {"withdrawn_avg": "avg", "withdrawn_peak_1in10": "peak"}
print("| Place | Cell land | Anchors used (km) | " + " | ".join(f"{d} {label[s]}" for d, s in STATS) + " | Design dry-bulb (C) |")
print("|---|---|---|" + "---|" * (len(STATS) + 1))
for r in rows:
    a = ", ".join(f"{n.split(' ')[0]} {k:.0f}" for n, k, _ in r["decided_anchors"]) or ("none within 100 km" if r["land"] < 0.9 else "-")
    cells = [" / ".join(f'{r["err"][w][f"{d}.{s}"]:+.0f}' for w in ("none", "shore", "decided")) for d, s in STATS]
    ddb = " / ".join(f'{r["err"][w]["design_db"]:+.1f}' for w in ("none", "shore", "decided")) if r["err"]["none"]["design_db"] is not None else "-"
    print(f'| {r["name"]}, {r["state"]} | {r["land"]:.2f} | {a} | ' + " | ".join(cells) + f" | {ddb} |")


def summary(sel, title):
    print(f"\n{title} ({len(sel)} places): median absolute % difference from the station (mean)\n")
    print("| Way | " + " | ".join(f"{d} {label[s]}" for d, s in STATS) + " |")
    print("|---|" + "---|" * len(STATS))
    for w in WAYS:
        cells = []
        for d, s in STATS:
            x = np.array([r["err"][w][f"{d}.{s}"] for r in sel])
            cells.append(f"{np.median(abs(x)):.0f}% ({x.mean():+.0f}%)")
        print(f"| {w} | " + " | ".join(cells) + " |")


summary(rows, "All 21")
summary([r for r in rows if r["geoid"] in SHORE], "The five shoreline places")
summary([r for r in rows if r["geoid"] not in SHORE], "The other 16")
