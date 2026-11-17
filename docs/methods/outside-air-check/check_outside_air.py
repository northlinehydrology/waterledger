"""Design 0022's check: the outside air design against operators' and LBNL's figures, at four places, in memory (nothing is written to the cache).

For each place: the cell's 30 years of station-corrected ERA5 weather (era5.weather, as the cell runs use it), 400 draws (seed 7) of the shared plant,
and the compiled heat balance (kernel.hourly_run) for the outside air design, (a) with every hall air-cooled (liquid_share 0, as Meta's and AWS's
disclosed fleets are) and (b) at the plant's own liquid share (0-1). Reported, as medians over the draws with the 10th-90th percentiles:
  PUE a year; consumed and withdrawn water per IT kWh, L (operators' WUE is withdrawal per IT kWh); the share of hours on the pads (above the
  setting); the share of hours with trim chillers running; and the hottest hour's PUE, the 90th percentile of the years' highest hourly PUE at the
  peak-day load (close to, not the same as, the cell records' pue_peak_1in10).
Towers and dry on the same draws are given beside it for (b).

Run from the waterledger repo root:  .venv/bin/python -B docs/methods/outside-air-check/check_outside_air.py > docs/methods/outside-air-check/check.md
"""
import json
import os

import numpy as np

from waterledger.national import era5 as E
from waterledger_models.datacenter import cooling, kernel, physics as ph

CELLS = {
    "Grand Rapids, MI": ("43.00_-85.75", "726350-94860,725396-14815+linked,726357-94815,725390-14836"),
    "Loudoun County, VA": ("39.00_-77.50", "724030-93738,724037-93728+linked,724050-13743,724177-13734"),
    "Dallas, TX": ("32.75_-96.75", "722599-03971,722590-03927,722541-53914,747390-13961"),
    "Phoenix, AZ": ("33.50_-112.00", "722780-23183,722784-03184,722785-23111+linked"),
}
L_GAL = 3.78541


def stations(ids):
    a = os.path.join(E.CACHE, "era5", "anchors")
    out = []
    for i in ids.split(","):
        meta = json.load(open(os.path.join(a, i + ".json")))
        out.append({**meta, "shore_land": meta.get("shore_land", meta["cell_land"]), "qt": np.load(os.path.join(a, f"{i}.t-td.npy"))})
    return out


def q(x):
    return np.percentile(x, [50, 10, 90])


def run(times, tdb, rh, design, draws, override=None):
    twb = ph.wet_bulb(tdb, rh)
    weather = kernel.weather_terms(tdb, twb)
    years = np.array([t[:4] for t in times])
    starts = np.r_[0, np.flatnonzero(years[1:] != years[:-1]) + 1]
    pue, wue_c, wue_w, pads, trim, peak = [], [], [], [], [], []
    for p0 in draws:
        p = ph.for_location({**p0, **(override or {})}, tdb)
        at_peak = {**p, "utilization": float(ph.peak_utilization(p))}
        out = kernel.hourly_run(tdb, twb, rh, weather, design, p, at_peak)
        pue.append(out[0].mean())
        wue_c.append(out[2].mean() * L_GAL)
        wue_w.append(out[1].mean() * L_GAL)
        yearly_max = np.maximum.reduceat(out[10], starts)
        peak.append(np.quantile(yearly_max, 0.9))
        if design == "outside_air":
            s = float(ph.outside_air_switch(p))
            pads.append(np.mean(tdb > s))
            h = ph.outside_air_hall(tdb, twb, p, rh)
            trim.append(np.mean(h["trim"] > 0))
    res = {"pue": q(pue), "wue_consumed": q(wue_c), "wue_withdrawn": q(wue_w), "peak_pue": q(peak)}
    if pads:
        res |= {"pad_hours": q(pads), "trim_hours": q(trim)}
    return res


def fmt(v, d=3, pct=False):
    m, lo, hi = v
    if pct:
        return f"{100 * m:.0f}% ({100 * lo:.0f}-{100 * hi:.0f})"
    return f"{m:.{d}f} ({lo:.{d}f}-{hi:.{d}f})"


def main():
    draws = cooling.sample(ph.DRAWS, E.SEED, "shared")
    print("| Place | Halls | PUE a year | Hottest-hour PUE | WUE consumed, L/kWh | WUE withdrawn, L/kWh | Hours on pads | Hours with trim chillers |")
    print("|---|---|---|---|---|---|---|---|")
    rows = []
    for name, (cid, ids) in CELLS.items():
        times, temps, rhs, note = E.weather(cid, stations(ids))
        tdb, rh = np.asarray(temps, dtype=float), np.asarray(rhs, dtype=float)
        for label, over in (("all air-cooled", {"liquid_share": 0.0}), ("plant's liquid share", None)):
            r = run(times, tdb, rh, "outside_air", draws, over)
            print(f"| {name} | {label} | {fmt(r['pue'])} | {fmt(r['peak_pue'])} | {fmt(r['wue_consumed'], 2)} | {fmt(r['wue_withdrawn'], 2)} | "
                  f"{fmt(r['pad_hours'], pct=True)} | {fmt(r['trim_hours'], pct=True)} |", flush=True)
        for d in ("dry", "towers"):
            r = run(times, tdb, rh, d, draws, None)
            rows.append(f"| {name} | {d} | {fmt(r['pue'])} | {fmt(r['peak_pue'])} | {fmt(r['wue_consumed'], 2)} | {fmt(r['wue_withdrawn'], 2)} |")
    print("\nThe same draws, the plant's liquid share:\n")
    print("| Place | Design | PUE a year | Hottest-hour PUE | WUE consumed, L/kWh | WUE withdrawn, L/kWh |")
    print("|---|---|---|---|---|---|")
    print("\n".join(rows))


if __name__ == "__main__":
    main()
