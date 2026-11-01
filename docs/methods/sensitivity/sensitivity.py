"""Global sensitivity analysis of the Water Ledger data center water model (cooling water and non-cooling water).

    python docs/methods/sensitivity/sensitivity.py            # full run, fixed seeds, writes CSVs next to this file
    python docs/methods/sensitivity/sensitivity.py --quick    # small N, prints only, for checking the script

Variance-based (Sobol') indices with the Saltelli (2010) radial design: first-order S1 by Saltelli et al. (2010),
total ST by Jansen (1999), percentile bootstrap 95% intervals. Elementary effects by Morris
(1991) on a four-level grid, with mu* (mean absolute effect) from Campolongo et al. (2007). Only numpy is used.

The parameter space is read at run time from waterledger_models.datacenter.physics (PARAMETERS, RANGES, TOPUP, ADIABATIC, STAFF), and the model is the
package's own physics.hourly_rates and physics.staff_water, so a change to a range, a new parameter or a change to the physics is
picked up by rerunning this script unchanged. The package is imported from this checkout (packages/*/src), not from whatever is
installed. Inputs are independent uniforms over each range, as in the package's Monte Carlo.

Outputs, per design (dry, assist, hybrid, towers), in gallons a day per 100 MW of IT capacity over the stored two-year West
Michigan test weather: annual average consumed, annual average withdrawn, and the 1-in-10-year peak-day withdrawn as the package
defines it (90th percentile of annual maximum days). Non-cooling water (staff plus maintenance) at 300 MW: withdrawn and consumed,
gallons a day.
"""
import argparse
import csv
import datetime as dt
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "packages" / "waterledger-models" / "src"))

from waterledger_models import MODEL_VERSION  # noqa: E402
from waterledger_models.datacenter import cooling as cw  # noqa: E402
from waterledger_models.datacenter import physics as ph  # noqa: E402

WEATHER = ROOT / "tests" / "data" / "west_michigan_2023_2024.json"
MW = 100.0                 # cooling outputs per 100 MW of IT capacity
NC_MW = 300.0              # non-cooling water at a 300 MW campus
SEED = 20261030
N_COOL = 8192              # Saltelli base sample per design: N (k + 2) model runs
N_STAFF = 2 ** 15
R_MORRIS = 100             # Morris trajectories
LEVELS = 4                 # Morris grid levels; step = LEVELS / (2 (LEVELS - 1)) = 2/3
N_BOOT = 1000
BATCH = 512
WATER_OUTPUTS = ("consumed_avg", "withdrawn_avg", "withdrawn_peak_1in10")
COOL_OUTPUTS = WATER_OUTPUTS + ("pue_avg", "pue_hottest_hour")       # model 1.4: electricity from the same heat balance
NC_OUTPUTS = ("nc_withdrawn", "nc_consumed")


# ---------------------------------------------------------------- parameter spaces (read from the package at run time)

def cooling_space():
    """[(name, low, high)] for the cooling model: physics.RANGES, topup and physics.ADIABATIC, in the order of physics.PARAMETERS. The
    package samples topup and ADIABATIC on their own streams; here all are independent uniforms on one design."""
    bounds = {**ph.RANGES, "topup": ph.TOPUP, **ph.ADIABATIC, **ph.POWER, **ph.OUTSIDE}
    return [(k, float(bounds[k][0]), float(bounds[k][1])) for k in ph.PARAMETERS]


def staff_space():
    return [(f"staff_{k}", float(a), float(b)) for k, (a, b) in ph.STAFF.items()]


def scale(u, space):
    lo = np.array([s[1] for s in space])
    hi = np.array([s[2] for s in space])
    return lo + (hi - lo) * u


# ---------------------------------------------------------------- the model

def load_weather():
    w = json.loads(WEATHER.read_text())
    t0 = dt.datetime.fromisoformat(w["start"])
    tdb = np.array(w["temperature_2m"], dtype=float)
    rh = np.array(w["relative_humidity_2m"], dtype=float)
    times = [(t0 + dt.timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M") for h in range(len(tdb))]
    if t0.hour != 0 or len(tdb) % 24:
        raise ValueError("the weather must be whole days starting at midnight")
    days = np.array([t[:10] for t in times[::24]])
    return {"times": times, "tdb": tdb, "rh": rh, "twb": ph.wet_bulb(tdb, rh), "days": days,
            "years": np.array([d[:4] for d in days]), "source": w.get("source", "")}


def cooling_outputs(wx, design, X, space):
    """X: (n, k) parameter values in physical units. Returns {output: (n,)} in gal/day per 100 MW of IT capacity (the constant MW)."""
    names = [s[0] for s in space]
    nd = len(wx["days"])
    out = {k: np.empty(len(X)) for k in COOL_OUTPUTS}
    ys = np.unique(wx["years"])
    for i in range(0, len(X), BATCH):
        xb = X[i:i + BATCH]
        p = {k: xb[:, j:j + 1] for j, k in enumerate(names)}
        w, c, _ = ph.hourly_rates(wx["tdb"], wx["twb"], design, p, wx["rh"])
        kw = MW * 1000.0 * p["utilization"]
        wd = (w * kw).reshape(len(xb), nd, 24).sum(-1)      # gal per day
        cd = (c * kw).reshape(len(xb), nd, 24).sum(-1)
        ann_max = np.stack([wd[:, wx["years"] == y].max(1) for y in ys], axis=1)
        out["consumed_avg"][i:i + BATCH] = cd.mean(1)
        out["withdrawn_avg"][i:i + BATCH] = wd.mean(1)
        out["withdrawn_peak_1in10"][i:i + BATCH] = np.quantile(ann_max, 0.9, axis=1)
        pue = ph.hourly_heat_power(wx["tdb"], wx["twb"], design, p, wx["rh"])[0]
        out["pue_avg"][i:i + BATCH] = pue.mean(1)
        out["pue_hottest_hour"][i:i + BATCH] = np.quantile(np.stack([pue[:, np.repeat(wx["years"], 24) == y].max(1) for y in ys], axis=1), 0.9, axis=1)
    return out


def staff_outputs(X, space):
    s = {k: X[:, j] for j, (k, _, _) in enumerate(space)}
    w, c, _ = ph.staff_water(s, NC_MW)
    return {"nc_withdrawn": w * 1e6, "nc_consumed": c * 1e6}


def check_against_package(wx, space, rng):
    """The vectorized daily statistics must equal cooling.daily_stats, the function behind the published numbers."""
    names = [s[0] for s in space]
    X = scale(rng.random((3, len(space))), space)
    _, day_index = np.unique([t[:10] for t in wx["times"]], return_inverse=True)
    for design in ph.DESIGNS:
        mine = cooling_outputs(wx, design, X, space)
        for r in range(len(X)):
            p = dict(zip(names, X[r]))
            w, c, _ = cw.hourly(wx["tdb"], wx["twb"], design, p, wx["rh"])
            kw = MW * 1000 * p["utilization"]
            sw = cw.daily_stats(day_index, len(wx["days"]), wx["years"], w, kw)
            sc = cw.daily_stats(day_index, len(wx["days"]), wx["years"], c, kw)
            got = [mine[k][r] / 1e6 for k in WATER_OUTPUTS]
            want = [sc["avg"], sw["avg"], sw["peak_1in10"]]
            np.testing.assert_allclose(got, want, rtol=1e-9, atol=1e-15)


# ---------------------------------------------------------------- Sobol' indices

def saltelli_runs(rng, n, k):
    """A, B and the k matrices AB_i (A with column i taken from B), stacked: (n (k + 2), k) in [0, 1)."""
    A, B = rng.random((n, k)), rng.random((n, k))
    AB = np.repeat(A[None], k, axis=0)
    for i in range(k):
        AB[i, :, i] = B[:, i]
    return np.concatenate([A, B, AB.reshape(n * k, k)])


def sobol_indices(yA, yB, yAB):
    """yA, yB: (..., n); yAB: (k, ..., n). S1 (Saltelli et al. 2010) and ST (Jansen 1999), each (k, ...)."""
    V = np.var(np.concatenate([yA, yB], axis=-1), axis=-1, ddof=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        S1 = np.mean(yB * (yAB - yA), axis=-1) / V
        ST = 0.5 * np.mean((yA - yAB) ** 2, axis=-1) / V
    return S1, ST


def analyse_sobol(y, n, k, rng_boot):
    """y: (n (k + 2),) model outputs in saltelli_runs order. Returns S1, ST (k,), their bootstrap 2.5/97.5 percentiles (2, k)
    and the convergence trace {n_sub: (S1, ST)} over nested subsamples. Outputs are centred on the mean of f(A) and f(B) first:
    the indices are unchanged in expectation, but the S1 estimator's sampling error otherwise grows with the output's mean."""
    y = y - y[:2 * n].mean()
    yA, yB, yAB = y[:n], y[n:2 * n], y[2 * n:].reshape(k, n)
    S1, ST = sobol_indices(yA, yB, yAB)
    idx = rng_boot.integers(0, n, size=(N_BOOT, n))
    bS1, bST = np.empty((k, N_BOOT)), np.empty((k, N_BOOT))
    for c in range(0, N_BOOT, 100):                                   # chunks keep memory small
        ic = idx[c:c + 100]
        bA, bB = yA[ic], yB[ic]
        for i in range(k):
            bS1[i, c:c + 100], bST[i, c:c + 100] = sobol_indices(bA, bB, yAB[i][ic])
    ci = {"S1": np.percentile(bS1, [2.5, 97.5], axis=1), "ST": np.percentile(bST, [2.5, 97.5], axis=1)}
    trace = {}
    m = n // 8
    while m <= n:
        trace[m] = sobol_indices(yA[:m], yB[:m], yAB[:, :m])
        m *= 2
    return S1, ST, ci, trace


# ---------------------------------------------------------------- Morris elementary effects

def morris_runs(rng, r, k, levels=LEVELS):
    """r random one-at-a-time trajectories of k + 1 points on a `levels`-level grid in [0, 1] (Morris 1991). Returns points
    (r (k + 1), k), the parameter moved at each step (r, k) and the signed step (r, k)."""
    delta = levels / (2.0 * (levels - 1))
    base_levels = np.arange(levels) / (levels - 1)
    base_levels = base_levels[base_levels <= 1 - delta + 1e-12]
    pts, order, steps = [], np.empty((r, k), int), np.empty((r, k))
    for t in range(r):
        x0 = rng.choice(base_levels, size=k)
        sign = rng.choice([-1.0, 1.0], size=k)
        x = np.where(sign > 0, x0, x0 + delta)
        perm = rng.permutation(k)
        traj = [x.copy()]
        for j in perm:
            x = x.copy()
            x[j] += sign[j] * delta
            traj.append(x)
        pts.append(np.array(traj))
        order[t], steps[t] = perm, sign[perm] * delta
    return np.concatenate(pts), order, steps


def analyse_morris(y, order, steps, k):
    r = len(order)
    y = y.reshape(r, k + 1)
    ee = np.empty((r, k))
    for t in range(r):
        ee[t, order[t]] = np.diff(y[t]) / steps[t]
    ee[np.abs(ee) < 1e-9 * np.abs(y).max()] = 0.0      # floating-point round-off from parameters that cancel (utilization in dry)
    return ee.mean(0), np.abs(ee).mean(0), ee.std(0, ddof=1)


# ---------------------------------------------------------------- driver

def run(quick=False):
    t_start = time.time()
    n_cool, n_staff, r_morris = (512, 4096, 20) if quick else (N_COOL, N_STAFF, R_MORRIS)
    wx = load_weather()
    cspace, sspace = cooling_space(), staff_space()
    kc, ks = len(cspace), len(sspace)
    rng = np.random.default_rng(SEED)
    check_against_package(wx, cspace, np.random.default_rng(SEED + 1))

    # One design matrix for every design (common random numbers), and one for the non-cooling term.
    Uc = saltelli_runs(rng, n_cool, kc)
    Us = saltelli_runs(rng, n_staff, ks)
    Mc, morder_c, mstep_c = morris_runs(rng, r_morris, kc)
    Ms, morder_s, mstep_s = morris_runs(rng, r_morris, ks)
    rng_boot = np.random.default_rng(SEED + 2)

    jobs = []   # (design, output, space, y_sobol, y_morris)
    for design in ph.DESIGNS:
        t0 = time.time()
        ys = cooling_outputs(wx, design, scale(Uc, cspace), cspace)
        ym = cooling_outputs(wx, design, scale(Mc, cspace), cspace)
        print(f"  {design:7s} {len(Uc) + len(Mc):7d} runs in {time.time() - t0:5.1f} s", flush=True)
        for o in COOL_OUTPUTS:
            jobs.append((design, o, cspace, n_cool, ys[o], ym[o], morder_c, mstep_c))
    ys, ym = staff_outputs(scale(Us, sspace), sspace), staff_outputs(scale(Ms, sspace), sspace)
    for o in NC_OUTPUTS:
        jobs.append(("non-cooling", o, sspace, n_staff, ys[o], ym[o], morder_s, mstep_s))

    rows, mrows, crows, srows, warnings = [], [], [], [], []
    for design, o, space, n, y, y_m, morder, mstep in jobs:
        k = len(space)
        S1, ST, ci, trace = analyse_sobol(y, n, k, rng_boot)
        mu, mu_star, sigma = analyse_morris(y_m, morder, mstep, k)
        base = y[:2 * n]
        sd = base.std(ddof=1)
        units = "kWh per IT kWh" if o.startswith("pue") else "gal/day per 100 MW IT" if design != "non-cooling" else f"gal/day at {NC_MW:.0f} MW IT"
        srows.append({"design": design, "output": o, "units": units, "mean": base.mean(), "sd": sd,
                      "p10": np.quantile(base, 0.1), "p50": np.quantile(base, 0.5), "p90": np.quantile(base, 0.9),
                      "sum_S1": np.nansum(S1), "sum_ST": np.nansum(ST), "n_base": n, "model_runs": len(y)})
        for j, (name, lo, hi) in enumerate(space):
            rows.append({"design": design, "output": o, "parameter": name, "low": lo, "high": hi,
                         "S1": S1[j], "S1_lo": ci["S1"][0, j], "S1_hi": ci["S1"][1, j],
                         "ST": ST[j], "ST_lo": ci["ST"][0, j], "ST_hi": ci["ST"][1, j]})
            mrows.append({"design": design, "output": o, "parameter": name, "mu": mu[j], "mu_star": mu_star[j], "sigma": sigma[j],
                          "mu_star_over_sd": mu_star[j] / sd if sd > 0 else np.nan,
                          "mu_star_rank": int((mu_star > mu_star[j]).sum()) + 1})
        for m, (s1m, stm) in trace.items():
            crows.append({"design": design, "output": o, "n_base": m, "model_runs": m * (k + 2),
                          "max_abs_dS1": np.nanmax(np.abs(s1m - S1)), "max_abs_dST": np.nanmax(np.abs(stm - ST)),
                          "sum_S1": np.nansum(s1m), "sum_ST": np.nansum(stm)})
        # sanity: indices in [0, 1] within noise, sum of S1 at most about 1, ST at least S1
        tol = 0.03
        if np.isfinite(S1).any():
            if (S1 < -tol).any() or (ST > 1 + tol).any() or (S1 > 1 + tol).any():
                warnings.append(f"{design}/{o}: an index is outside [0, 1] by more than {tol}")
            if np.nansum(S1) > 1 + tol:
                warnings.append(f"{design}/{o}: sum of S1 = {np.nansum(S1):.3f}")
            if (ST < S1 - tol).any():
                warnings.append(f"{design}/{o}: ST < S1 for " + ", ".join(np.array([s[0] for s in space])[ST < S1 - tol]))

    def write(name, data):
        with open(HERE / name, "w", newline="") as f:
            wr = csv.DictWriter(f, fieldnames=list(data[0]))
            wr.writeheader()
            for d in data:
                wr.writerow({k: (f"{v:.6g}" if isinstance(v, (float, np.floating)) else v) for k, v in d.items()})

    if not quick:
        write("sobol_indices.csv", rows)
        write("morris.csv", mrows)
        write("convergence.csv", crows)
        write("output_summary.csv", srows)
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    except OSError:
        commit = ""
    runtime = time.time() - t_start
    info = {"model_version": MODEL_VERSION, "code_commit": commit, "numpy": np.__version__, "seed": SEED,
            "weather": wx["source"], "hours": len(wx["tdb"]), "n_base_cooling": n_cool, "n_base_noncooling": n_staff,
            "morris_trajectories": r_morris, "morris_levels": LEVELS, "bootstrap": N_BOOT,
            "model_runs_per_design": n_cool * (kc + 2) + r_morris * (kc + 1),
            "cooling_parameters": {n: [lo, hi] for n, lo, hi in cspace},
            "noncooling_parameters": {n: [lo, hi] for n, lo, hi in sspace},
            "runtime_s": round(runtime, 1), "quick": quick, "warnings": warnings}
    if not quick:
        (HERE / "run_info.json").write_text(json.dumps(info, indent=1) + "\n")

    print(f"\nmodel {MODEL_VERSION}, N = {n_cool} (cooling, {kc} parameters), {n_staff} (non-cooling, {ks}), "
          f"Morris r = {r_morris}, {runtime:.0f} s\n")
    for s in srows:
        sub = [r for r in rows if r["design"] == s["design"] and r["output"] == s["output"]]
        sub.sort(key=lambda r: -np.nan_to_num(r["ST"]))
        top = "; ".join(f"{r['parameter']} {r['ST']:.2f} [{r['ST_lo']:.2f}, {r['ST_hi']:.2f}] (S1 {r['S1']:.2f})" for r in sub[:3])
        print(f"{s['design']:11s} {s['output']:21s} mean {s['mean']:9.0f}  sum S1 {s['sum_S1']:.2f}  top ST: {top}")
    print("\nwarnings:", *(warnings or ["none"]), sep="\n  ")
    return info


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--quick", action="store_true", help="small sample sizes, prints only, for checking the script")
    run(ap.parse_args().quick)
