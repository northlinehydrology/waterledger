"""Global sensitivity analysis of the battery cell plant model (design 0009), on the data center analysis's method.

    python docs/methods/sensitivity/battery/sensitivity.py            # full run, fixed seeds, writes CSVs next to this file
    python docs/methods/sensitivity/battery/sensitivity.py --quick    # small N, prints only, for checking the script

Sobol' indices (Saltelli et al. 2010 for S1, Jansen 1999 for ST, percentile bootstrap 95% intervals) and Morris elementary effects, with the
functions of ../sensitivity.py unchanged. The parameter space is read at run time from waterledger_models.battery.physics (RANGES, the
shared heat_rejection.EQUIPMENT and once_through.RANGES), and the model is physics.hourly, so a change to a range or to the physics is picked
up by rerunning this script. The package is imported from this checkout. Inputs are independent uniforms over each range.

The plant runs at full output, the headline (design 0009, decision 2), so utilization is not a factor, and it makes NMC cells (an LFP plant
scales the plant energy by lfp_factor, which would lead every output). Outputs, per design (dry, hybrid, towers, lake), per 10 GWh/yr of cell
capacity over the stored two-year West Michigan test weather (and GLERL's Lake Michigan temperatures for the lake): annual average consumed,
withdrawn and sent to the sewer, the 1-in-10-year peak-day withdrawn, in gallons a day; average electricity and the 1-in-10-year highest
hour of it, in MW.
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
from waterledger_models import once_through as ot  # noqa: E402
from waterledger_models.battery import physics as bp  # noqa: E402
from waterledger_models.battery import plant  # noqa: E402
from waterledger_models.daily import daily_stats  # noqa: E402

GWH = 10.0
SEED = 20261110
N_BASE = 4096
R_MORRIS = 100
BATCH = 96
LAKE = ROOT / "tests" / "data" / "water_ledger_lakes.json"
OUTPUTS = ("consumed_avg", "withdrawn_avg", "to_sewer_avg", "withdrawn_peak_1in10", "power_mw_avg", "power_mw_peak_1in10")
UNITS = {"power_mw_avg": "MW per 10 GWh/yr", "power_mw_peak_1in10": "MW per 10 GWh/yr"}


def space(design):
    """[(name, low, high)]: the plant's own ranges less utilization, the shared equipment's, and the lake's for the lake design."""
    r = {**{k: v for k, v in bp.RANGES.items() if k != "utilization"}, **hr.EQUIPMENT, **(ot.RANGES if design == "lake" else {})}
    return [(k, float(a), float(b)) for k, (a, b) in r.items()]


def weather():
    wx = sa.load_weather()
    wx["water_t"] = plant.lake_hours(wx["times"], json.loads(LAKE.read_text())["Lake Michigan"]["temps"])
    return wx


def outputs(wx, design, X, sp):
    """X: (n, k) parameter values. Returns {output: (n,)}: gal/day and MW per GWH GWh/yr of capacity."""
    names = [s[0] for s in sp]
    nd = len(wx["days"])
    ys = np.unique(wx["years"])
    hour_years = np.repeat(wx["years"], 24)
    peak = lambda a, years: np.quantile(np.stack([a[:, years == y].max(1) for y in ys], axis=1), 0.9, axis=1)
    out = {k: np.empty(len(X)) for k in OUTPUTS}
    for i in range(0, len(X), BATCH):
        xb = X[i:i + BATCH]
        p = bp.for_location({**{k: xb[:, j:j + 1] for j, k in enumerate(names)}, "utilization": 1.0}, wx["tdb"], wx["rh"])
        h = bp.hourly(wx["tdb"], wx["twb"], wx["rh"], design, p, wx["water_t"])
        day = lambda name: np.broadcast_to(h[name], (len(xb), len(wx["tdb"]))).reshape(len(xb), nd, 24).sum(-1) * GWH
        w = day("withdrawn")
        out["withdrawn_avg"][i:i + BATCH] = w.mean(1)
        out["withdrawn_peak_1in10"][i:i + BATCH] = peak(w, wx["years"])
        out["consumed_avg"][i:i + BATCH] = day("consumed").mean(1)
        out["to_sewer_avg"][i:i + BATCH] = day("to_sewer").mean(1)
        e = h["electricity"] * GWH / 1000.0
        out["power_mw_avg"][i:i + BATCH] = e.mean(1)
        out["power_mw_peak_1in10"][i:i + BATCH] = peak(e, hour_years)
    return out


def check_against_package(wx, rng):
    """The batched outputs must equal physics.hourly run one parameter set at a time through daily.daily_stats and plant.run_location's rule
    for the highest hour, the functions behind the package's numbers."""
    _, day_index = np.unique([t[:10] for t in wx["times"]], return_inverse=True)
    year_ends = np.r_[np.flatnonzero(np.repeat(wx["years"], 24)[1:] != np.repeat(wx["years"], 24)[:-1]) + 1, len(wx["tdb"])]
    for design in bp.DESIGNS:
        sp = space(design)
        X = sa.scale(rng.random((3, len(sp))), sp)
        mine = outputs(wx, design, X, sp)
        for r in range(len(X)):
            p = bp.for_location({**dict(zip([s[0] for s in sp], X[r])), "utilization": 1.0}, wx["tdb"], wx["rh"])
            h = bp.hourly(wx["tdb"], wx["twb"], wx["rh"], design, p, wx["water_t"])
            st = lambda name: daily_stats(day_index, len(wx["days"]), wx["years"], h[name], GWH)
            want = [st("consumed")["avg"], st("withdrawn")["avg"], st("to_sewer")["avg"], st("withdrawn")["peak_1in10"],
                    h["electricity"].mean() * GWH / 1000,
                    np.quantile([a.max() for a in np.split(h["electricity"], year_ends[:-1])], 0.9) * GWH / 1000]
            got = [mine[k][r] / (1e6 if not k.startswith("power") else 1.0) for k in OUTPUTS]
            np.testing.assert_allclose(got, want, rtol=1e-9, atol=1e-15)


def run(quick=False):
    t_start = time.time()
    n, r_morris = (256, 10) if quick else (N_BASE, R_MORRIS)
    wx = weather()
    check_against_package(wx, np.random.default_rng(SEED + 1))
    rng_boot = np.random.default_rng(SEED + 2)
    rows, mrows, crows, srows, warnings, runs = [], [], [], [], [], {}
    for design in bp.DESIGNS:
        sp = space(design)
        k = len(sp)
        rng = np.random.default_rng(SEED)        # the same draws for every design over the parameters they share
        U, (M, order, steps) = sa.saltelli_runs(rng, n, k), sa.morris_runs(rng, r_morris, k)
        t0 = time.time()
        ys, ym = outputs(wx, design, sa.scale(U, sp), sp), outputs(wx, design, sa.scale(M, sp), sp)
        runs[design] = len(U) + len(M)
        print(f"  {design:7s} {runs[design]:7d} runs in {time.time() - t0:6.1f} s", flush=True)
        for o in OUTPUTS:
            y = ys[o]
            S1, ST, ci, trace = sa.analyse_sobol(y, n, k, rng_boot)
            mu, mu_star, sigma = sa.analyse_morris(ym[o], order, steps, k)
            base = y[:2 * n]
            sd = base.std(ddof=1)
            srows.append({"design": design, "output": o, "units": UNITS.get(o, "gal/day per 10 GWh/yr"), "mean": base.mean(), "sd": sd,
                          "p10": np.quantile(base, 0.1), "p50": np.quantile(base, 0.5), "p90": np.quantile(base, 0.9),
                          "sum_S1": np.nansum(S1), "sum_ST": np.nansum(ST), "n_base": n, "model_runs": len(y)})
            for j, (name, lo, hi) in enumerate(sp):
                rows.append({"design": design, "output": o, "parameter": name, "low": lo, "high": hi,
                             "S1": S1[j], "S1_lo": ci["S1"][0, j], "S1_hi": ci["S1"][1, j],
                             "ST": ST[j], "ST_lo": ci["ST"][0, j], "ST_hi": ci["ST"][1, j]})
                mrows.append({"design": design, "output": o, "parameter": name, "mu": mu[j], "mu_star": mu_star[j], "sigma": sigma[j],
                              "mu_star_over_sd": mu_star[j] / sd if sd > 0 else np.nan, "mu_star_rank": int((mu_star > mu_star[j]).sum()) + 1})
            for m, (s1m, stm) in trace.items():
                crows.append({"design": design, "output": o, "n_base": m, "model_runs": m * (k + 2),
                              "max_abs_dS1": np.nanmax(np.abs(s1m - S1)), "max_abs_dST": np.nanmax(np.abs(stm - ST)),
                              "sum_S1": np.nansum(s1m), "sum_ST": np.nansum(stm)})
            tol = 0.03
            if np.isfinite(S1).any():
                if (S1 < -tol).any() or (ST > 1 + tol).any() or (S1 > 1 + tol).any():
                    warnings.append(f"{design}/{o}: an index is outside [0, 1] by more than {tol}")
                if np.nansum(S1) > 1 + tol:
                    warnings.append(f"{design}/{o}: sum of S1 = {np.nansum(S1):.3f}")
                if (ST < S1 - tol).any():
                    warnings.append(f"{design}/{o}: ST < S1 for " + ", ".join(np.array([s[0] for s in sp])[ST < S1 - tol]))

    def write(name, data):
        with open(HERE / name, "w", newline="") as f:
            wr = csv.DictWriter(f, fieldnames=list(data[0]))
            wr.writeheader()
            for d in data:
                wr.writerow({k: (f"{v:.6g}" if isinstance(v, (float, np.floating)) else v) for k, v in d.items()})

    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    runtime = time.time() - t_start
    info = {"model": "battery cell plants, design 0009", "code_commit": commit, "numpy": np.__version__, "seed": SEED, "weather": wx["source"],
            "hours": len(wx["tdb"]), "gwh": GWH, "utilization": 1.0, "chemistry": "nmc", "n_base": n, "morris_trajectories": r_morris,
            "morris_levels": sa.LEVELS, "bootstrap": sa.N_BOOT, "model_runs": runs,
            "parameters": {d: {nm: [lo, hi] for nm, lo, hi in space(d)} for d in bp.DESIGNS}, "runtime_s": round(runtime, 1), "warnings": warnings}
    if not quick:
        write("sobol_indices.csv", rows)
        write("morris.csv", mrows)
        write("convergence.csv", crows)
        write("output_summary.csv", srows)
        (HERE / "run_info.json").write_text(json.dumps(info, indent=1) + "\n")
    print(f"\nN = {n}, Morris r = {r_morris}, {runtime:.0f} s\n")
    for s in srows:
        sub = sorted((r for r in rows if r["design"] == s["design"] and r["output"] == s["output"]), key=lambda r: -np.nan_to_num(r["ST"]))
        top = "; ".join(f"{r['parameter']} {r['ST']:.2f} [{r['ST_lo']:.2f}, {r['ST_hi']:.2f}] (S1 {r['S1']:.2f})" for r in sub[:4])
        print(f"{s['design']:7s} {s['output']:21s} mean {s['mean']:10.1f}  sum S1 {s['sum_S1']:.2f}  top ST: {top}")
    print("\nwarnings:", *(warnings or ["none"]), sep="\n  ")
    return info


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--quick", action="store_true", help="small sample sizes, prints only, for checking the script")
    run(ap.parse_args().quick)
