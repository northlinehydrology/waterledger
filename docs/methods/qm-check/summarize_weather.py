"""Tables of cv_weather.json: median absolute error (mean error) against the held-out station, by way of carrying the correction."""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(HERE, "cv_weather.json")))
R = d["rows"]
K = [("ddb", "Design dry-bulb (C)"), ("wb", "0.4% wet bulb (C)"), ("summer_pm", "Summer afternoon T (C)"), ("td", "Mean dew point (C)")]


def table(rows, label):
    print(f"\n{label} ({len(rows)} stations): median absolute error (mean error) against the held-out station\n")
    print("| Way | " + " | ".join(t for _, t in K) + " | Quantile MAE, T / Td (C) |")
    print("|---|" + "---|" * (len(K) + 1))
    for w in d["ways"]:
        e = [r["errors"][w] for r in rows]
        cells = []
        for k, _ in K:
            x = np.array([v[k] for v in e])
            cells.append(f"{np.median(abs(x)):.2f} ({x.mean():+.2f})")
        cells.append(f'{np.median([v["q_mae_t"] for v in e]):.2f} / {np.median([v["q_mae_td"] for v in e]):.2f}')
        print(f"| {w} | " + " | ".join(cells) + " |")


ok = [r for r in R if r["errors"]["bias"]["corrected"]]
print(len(R), "stations;", len(ok), "with another station within 100 km;", "not:", ", ".join(r["name"] for r in R if r not in ok))
table(ok, "Every station with a neighbor within 100 km")
table([r for r in ok if r["cell_land"] < 0.9], "Stations whose cell is under 90% land")
table([r for r in ok if r["cell_land"] >= 0.9], "Stations whose cell is at least 90% land")

# The rule decided Nov 4, 2026: shore stations only, so the cells it corrects are the shore stations with another shore station near
WAYS = ["none", "lapse_isd", "lapse", "lapse_shore_isd", "lapse_shore"]
d["ways"] = WAYS
dec = [r for r in R if r["cell_land"] < 0.9 and r["errors"]["lapse_shore"]["corrected"]]
table(dec, "Shore stations the decided rule corrects (another shore station within 100 km)")
print("\n| Station | Source | Cell land | Design dry-bulb error, none / lapse (any) / lapse_shore (C) | 0.4% wet bulb (C) |")
print("|---|---|---|---|---|")
for r in sorted(R, key=lambda r: r["cell_land"]):
    if r["cell_land"] < 0.9:
        e = r["errors"]
        f = lambda k: " / ".join(f'{e[w][k]:+.1f}' if e[w]["corrected"] or w == "none" else "-" for w in ("none", "lapse", "lapse_shore"))
        print(f'| {r["name"]}, {r["state"]} | {r.get("source")} | {r["cell_land"]:.2f} | {f("ddb")} | {f("wb")} |')
