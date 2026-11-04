"""The markdown tables for the land rule in era5-station-check.md, from land_rule_results.json. Usage: python land_rule_tables.py"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(HERE, "land_rule_results.json")))
pct = lambda a, b: f"{100 * (a / b - 1):+.0f}%"
KIND = [("nearest", "Nearest cell"), ("rule", "Land rule"), ("land_0.9", "At least 90% land (sensitivity)")]
print("| Place | Station (km) | " + " | ".join(f"{t} (km, land)" for _, t in KIND) + " |")
print("|---|---|" + "---|" * len(KIND))
for r in d["rows"]:
    s = r["nearest_station"]
    print(f'| {r["name"]}, {r["state"]} | {s["name"].replace(" International Ap", " Intl").replace(" Airport", "")} ({s["km"]:.0f}) | '
          + " | ".join(f'{r["cells"][k]["cell"].replace("_", ", ")} ({r["cells"][k]["km"]:.0f}, {r["cells"][k]["land"]:.2f})' for k, _ in KIND) + " |")
for stat, title in (("withdrawn_avg", "average day"), ("withdrawn_peak_1in10", "1-in-10 peak day")):
    print(f"\n#### Against the nearest station, {title} (p50, per 100 MW): nearest cell / land rule / at least 90% land\n")
    print("| Place | Towers | Hybrid | Assist |")
    print("|---|---|---|---|")
    for r in d["rows"]:
        s = r["station"]
        cells = [" / ".join(pct(r["era5"][k][f"{des}.{stat}"], s[f"{des}.{stat}"]) for k, _ in KIND) for des in ("towers", "hybrid", "assist")]
        print(f'| {r["name"]} | ' + " | ".join(cells) + " |")
print("\n| Place | Design dry-bulb, station (C) | Nearest cell | Land rule | At least 90% land |")
print("|---|---|---|---|---|")
for r in d["rows"]:
    print(f'| {r["name"]} | {format(r["station"]["design_db"], ".1f") if "design_db" in r["station"] else "not run"} | ' + " | ".join(f'{r["era5"][k]["design_db"]:.1f}' for k, _ in KIND) + " |")
