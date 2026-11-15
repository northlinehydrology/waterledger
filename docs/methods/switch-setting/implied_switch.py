"""The switch setting each operator's stated share of the year on water implies (design 0016, model 1.16).

    python docs/methods/switch-setting/implied_switch.py [--cache DIR]

For each site, the dry-bulb exceeded for the stated share of the year's hours (or, for a number of days, the daily maximum exceeded on that
many days a year), from Open-Meteo's archive (ERA5-based) hourly 2 m temperature at the site's point, 2015-2024. One request per site, cached.
Writes implied.md beside this script.
"""
import argparse, json, os, urllib.request

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
Y0, Y1 = 2015, 2024
# site, operator, lat, lon, kind, stated value, bound ("=" a stated figure, "<" an upper bound on the share, so the setting is at least what it implies), source
SITES = [
    ("Northern Virginia (Ashburn)", "Microsoft, direct air", 39.04, -77.49, "share", 0.10, "=", "Microsoft, June 24, 2026: about 10% of the year"),
    ("Phoenix", "Microsoft, direct air", 33.45, -112.07, "share", 0.40, "<", "Microsoft, June 24, 2026: up to 40%"),
    ("Mount Pleasant, WI", "Microsoft", 42.70, -87.89, "share", 0.05, "<", "Microsoft Wisconsin: less than 5% of the year"),
    ("Metro Atlanta", "Microsoft", 33.75, -84.39, "days", 55, "=", "Microsoft local, about Jan 2026: the hottest ~55 days"),
    ("Sidney, OH", "AWS", 40.28, -84.16, "share", 0.03, "=", "City of Sidney data center FAQ, 2026: about 3% of the year"),
    ("Falls Township, PA", "AWS", 40.17, -74.79, "share", 0.06, "=", "LevittownNow, July 28, 2026: outside air about 94% of the year"),
    ("New Carlisle, IN", "AWS", 41.70, -86.50, "days", 7, "=", "TheStatehouseFile (AWS statement), 2026: about 7 days a year"),
]


def temperatures(lat, lon, cache):
    os.makedirs(cache, exist_ok=True)
    path = os.path.join(cache, f"{lat:.2f}_{lon:.2f}_{Y0}_{Y1}.json")
    if not os.path.exists(path):
        url = (f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={Y0}-01-01&end_date={Y1}-12-31"
               "&hourly=temperature_2m,relative_humidity_2m&timezone=UTC")
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "waterledger"}), timeout=120) as r:
            open(path, "wb").write(r.read())
    h = json.load(open(path))["hourly"]
    keep = [(x, v) for x, v in zip(h["time"], h["temperature_2m"]) if v is not None]
    return [x for x, _ in keep], np.array([v for _, v in keep], float)


def implied(times, t, kind, value):
    if kind == "share":
        return float(np.quantile(t, 1.0 - value))
    daily = {}
    for x, v in zip(times, t):
        daily[x[:10]] = max(daily.get(x[:10], -99.0), v)
    return float(np.quantile(np.array(list(daily.values())), 1.0 - value / 365.25))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=os.path.join(HERE, ".cache"))
    a = ap.parse_args()
    lines = ["# Switch settings implied by operators' stated time on water", "",
             f"Open-Meteo archive (ERA5-based) hourly 2 m dry-bulb at each point, {Y0}-{Y1} (`implied_switch.py`). A share of the year is read as a share",
             "of hours; a number of days as days whose hottest hour is above the setting. \"At least\" where the operator gives an upper bound.", "",
             "| Site | Operator | Stated | Implied setting, C (F) | Source |", "|---|---|---|---|---|"]
    for site, op, lat, lon, kind, value, bound, src in SITES:
        times, t = temperatures(lat, lon, a.cache)
        s = implied(times, t, kind, value)
        stated = f"{'under ' if bound == '<' else ''}{value:.0%} of the year" if kind == "share" else f"{value} days a year"
        lines.append(f"| {site} | {op} | {stated} | {'at least ' if bound == '<' else ''}{s:.1f} ({s * 1.8 + 32:.1f}) | {src} |")
    lines += ["", "Stated settings: Microsoft 85 F (29.4 C), June 24, 2026; Meta El Paso about 86 F (30 C), El Paso Water's chief executive (El Paso Matters,",
              "Oct 24, 2025). The model samples 26.5-32.0 C (`switch_setting`), the lowest and highest of the figures above.", ""]
    open(os.path.join(HERE, "implied.md"), "w").write("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
