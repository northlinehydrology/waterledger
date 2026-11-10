"""Global sensitivity analysis of the gas plant model (design 0014), on the data center analysis's method.

    python docs/methods/sensitivity/gas/sensitivity.py            # full run, fixed seeds, writes CSVs next to this file
    python docs/methods/sensitivity/gas/sensitivity.py --quick    # small N, prints only, for checking the script

Sobol' indices (Saltelli et al. 2010 for S1, Jansen 1999 for ST, percentile bootstrap 95% intervals) and Morris elementary effects, with the
functions of ../sensitivity.py unchanged. The parameter space is read at run time from waterledger_models.gas.physics.ranges, and the model is
physics.hourly, so a change to a range or to the physics is picked up by rerunning this script. Inputs are independent uniforms over each range.

Each case is one hypothetical plant, two 300 MW units asked for their full ISO rating every hour, over the stored two-year West Michigan test
weather (and GLERL's Lake Michigan temperatures for the lake): combined cycle on towers, hybrid and the lake, and a simple-cycle turbine with water
injection. Outputs: water consumed and withdrawn per MWh net, gal/MWh; heat rate, Btu/kWh (fuel over net, HHV); and net output, MW. Dry
combined cycle, engines and fuel cells use no water to speak of and are left out.
"""
import argparse
import csv
import importlib.util
import json
import subprocess
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
_spec = importlib.util.spec_from_file_location("dc_sensitivity", HERE.parent / "sensitivity.py")   # also puts this checkout's package first
sa = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sa)

from waterledger_models import heat_rejection as hr  # noqa: E402
from waterledger_models.battery.plant import lake_hours  # noqa: E402
from waterledger_models.gas import physics as gp  # noqa: E402

SEED = 20261111
N_BASE = 2048
R_MORRIS = 100
BATCH = 128
UNITS, UNIT_MW = 2, 300.0
LAKE = ROOT / "tests" / "data" / "water_ledger_lakes.json"
CASES = {"cc_towers": ("cc", "towers", "dln"), "cc_hybrid": ("cc", "hybrid", "dln"), "cc_lake": ("cc", "lake", "dln"), "ct_water": ("ct", "none", "water")}
OUTPUTS = ("consumed_gal_per_mwh", "withdrawn_gal_per_mwh", "heat_rate", "net_mw_avg")
UNITS_OF = {"consumed_gal_per_mwh": "gal/MWh", "withdrawn_gal_per_mwh": "gal/MWh", "heat_rate": "Btu/kWh HHV", "net_mw_avg": "MW"}


def space(case):
    tech, design, nox = CASES[case]
    return [(k, float(a), float(b)) for k, (a, b) in gp.ranges(tech, design, nox).items() if a != b]


def weather():
    wx = sa.load_weather()
    wx["water_t"] = lake_hours(wx["times"], json.loads(LAKE.read_text())["Lake Michigan"]["temps"])
    wx["design_db"] = hr.design_dry_bulb(wx["tdb"])
    return wx


def outputs(wx, case, X, sp):
    tech, design, nox = CASES[case]
    names = [s[0] for s in sp]
    fixed = {**gp.central_parameters(tech, design, nox), "design_db": wx["design_db"]}
    out = {k: np.empty(len(X)) for k in OUTPUTS}
    for i in range(0, len(X), BATCH):
        xb = X[i:i + BATCH]
        p = {**fixed, **{k: xb[:, j:j + 1] for j, k in enumerate(names)}}
        h = gp.hourly(UNITS * UNIT_MW, wx["tdb"], wx["twb"], wx["rh"], tech, design, p, UNITS, UNIT_MW, water_t=wx["water_t"])
        served = np.broadcast_to(h["served"], (len(xb), len(wx["tdb"]))).sum(1)
        tot = lambda k: np.broadcast_to(h[k], (len(xb), len(wx["tdb"]))).sum(1)
        out["consumed_gal_per_mwh"][i:i + BATCH] = tot("consumed") / served
        out["withdrawn_gal_per_mwh"][i:i + BATCH] = tot("withdrawn") / served
        out["heat_rate"][i:i + BATCH] = tot("fuel") / served * gp.KWH_BTU
        out["net_mw_avg"][i:i + BATCH] = served / len(wx["tdb"])
    return out


def check_against_package(wx, rng):
    """The batched outputs must equal physics.hourly run one parameter set at a time."""
    for case, (tech, design, nox) in CASES.items():
        sp = space(case)
        X = sa.scale(rng.random((3, len(sp))), sp)
        mine = outputs(wx, case, X, sp)
        for r in range(len(X)):
            p = {**gp.central_parameters(tech, design, nox), "design_db": wx["design_db"], **dict(zip([s[0] for s in sp], X[r]))}
            h = gp.hourly(UNITS * UNIT_MW, wx["tdb"], wx["twb"], wx["rh"], tech, design, p, UNITS, UNIT_MW, water_t=wx["water_t"])
            s = h["served"].sum()
            want = [h["consumed"].sum() / s, h["withdrawn"].sum() / s, h["fuel"].sum() / s * gp.KWH_BTU, s / len(wx["tdb"])]
            np.testing.assert_allclose([mine[k][r] for k in OUTPUTS], want, rtol=1e-9)


def run(quick=False):
    t_start = time.time()
    n, r_morris = (128, 10) if quick else (N_BASE, R_MORRIS)
    wx = weather()
    check_against_package(wx, np.random.default_rng(SEED + 1))
    rng_boot = np.random.default_rng(SEED + 2)
    rows, mrows, srows, warnings, runs = [], [], [], [], {}
    for case in CASES:
        sp = space(case)
        k = len(sp)
        rng = np.random.default_rng(SEED)
        U, (M, order, steps) = sa.saltelli_runs(rng, n, k), sa.morris_runs(rng, r_morris, k)
        t0 = time.time()
        ys, ym = outputs(wx, case, sa.scale(U, sp), sp), outputs(wx, case, sa.scale(M, sp), sp)
        runs[case] = len(U) + len(M)
        print(f"  {case:10s} {runs[case]:7d} runs in {time.time() - t0:6.1f} s", flush=True)
        for o in OUTPUTS:
            y = ys[o]
            S1, ST, ci, _ = sa.analyse_sobol(y, n, k, rng_boot)
            mu, mu_star, sigma = sa.analyse_morris(ym[o], order, steps, k)
            base = y[:2 * n]
            sd = base.std(ddof=1)
            srows.append({"case": case, "output": o, "units": UNITS_OF[o], "mean": base.mean(), "sd": sd, "p10": np.quantile(base, 0.1),
                          "p50": np.quantile(base, 0.5), "p90": np.quantile(base, 0.9), "sum_S1": np.nansum(S1), "n_base": n})
            for j, (name, lo, hi) in enumerate(sp):
                rows.append({"case": case, "output": o, "parameter": name, "low": lo, "high": hi, "S1": S1[j], "S1_lo": ci["S1"][0, j],
                             "S1_hi": ci["S1"][1, j], "ST": ST[j], "ST_lo": ci["ST"][0, j], "ST_hi": ci["ST"][1, j]})
                mrows.append({"case": case, "output": o, "parameter": name, "mu_star": mu_star[j], "sigma": sigma[j],
                              "mu_star_over_sd": mu_star[j] / sd if sd > 0 else np.nan})
            if np.isfinite(S1).any() and np.nansum(S1) > 1.03:
                warnings.append(f"{case}/{o}: sum of S1 = {np.nansum(S1):.3f}")

    def write(name, data):
        with open(HERE / name, "w", newline="") as f:
            wr = csv.DictWriter(f, fieldnames=list(data[0]))
            wr.writeheader()
            for d in data:
                wr.writerow({k: (f"{v:.6g}" if isinstance(v, (float, np.floating)) else v) for k, v in d.items()})

    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    info = {"model": "gas plants, design 0014", "code_commit": commit, "seed": SEED, "weather": wx["source"], "hours": len(wx["tdb"]),
            "units": UNITS, "unit_mw": UNIT_MW, "n_base": n, "morris_trajectories": r_morris, "model_runs": runs,
            "parameters": {c: {nm: [lo, hi] for nm, lo, hi in space(c)} for c in CASES}, "runtime_s": round(time.time() - t_start, 1),
            "warnings": warnings}
    if not quick:
        write("sobol_indices.csv", rows)
        write("morris.csv", mrows)
        write("output_summary.csv", srows)
        (HERE / "run_info.json").write_text(json.dumps(info, indent=1) + "\n")
    for s in srows:
        sub = sorted((r for r in rows if r["case"] == s["case"] and r["output"] == s["output"]), key=lambda r: -np.nan_to_num(r["ST"]))
        top = "; ".join(f"{r['parameter']} {r['ST']:.2f}" for r in sub[:4])
        print(f"{s['case']:10s} {s['output']:22s} p50 {s['p50']:10.1f}  top ST: {top}")
    print("\nwarnings:", *(warnings or ["none"]), sep="\n  ")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--quick", action="store_true")
    run(ap.parse_args().quick)
