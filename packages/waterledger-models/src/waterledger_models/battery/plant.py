"""The battery cell plant Monte Carlo at one location (design 0009, model 1.12): every draw's hours through physics.hourly, then daily totals and
their statistics, per `gwh` GWh/yr of cell capacity.

utilization="full" (the headline, as every EA states its figure) runs every draw at full output; "sampled" draws it (physics.RANGES) for a
running plant. The peak day is the 1-in-10-year peak day (the 90th percentile of annual maxima) at the same output: a cell plant's output does
not follow the weather, so its peak is the weather's, through the towers and the outdoor air.
"""
import numpy as np

from waterledger_models import heat_rejection as hr
from waterledger_models.battery import physics as bp
from waterledger_models.daily import daily_stats, groups

DRAWS = 400       # as for data centers (datacenter.physics.DRAWS)
UTILIZATION = ("full", "sampled")


def draws(n=DRAWS, seed=7, utilization="full"):
    """The Monte Carlo draws, run by run, then the central run last: [{name: value}]."""
    if utilization not in UTILIZATION:
        raise ValueError(f"utilization must be one of {UTILIZATION}, not {utilization!r}")
    v = bp.sample_parameters(n, seed)
    runs = [{k: float(a[i]) for k, a in v.items()} for i in range(n)] + [bp.central_parameters()]
    return [{**p, "utilization": 1.0} for p in runs] if utilization == "full" else runs


def run_location(times, temps, rhs, n=DRAWS, seed=7, gwh=1.0, utilization="full", designs=bp.DESIGNS):
    """Monte Carlo for each design at one location, per `gwh` GWh/yr of cell capacity.

    Returns {design: {stat: {"p10", "p50", "p90", "central"}}}: withdrawn, consumed and returned (MGD) as avg, peak_1in10, record, annual_mg
    and, for withdrawn and consumed, max_month, max_90day and worst_year_mg; power_mw_avg and power_mw_peak_day_1in10 (electricity, MW); fuel_mw_avg;
    site_kwh_per_kwh (electricity and fuel per kWh of cells made, the cooling plant included); withdrawn_l_per_kwh and consumed_l_per_kwh (per kWh
    of cells made); utilization.
    """
    tdb, rh = np.array(temps, dtype=float), np.array(rhs, dtype=float)
    twb = hr.wet_bulb(tdb, rh)
    days = np.array([t[:10] for t in times])
    uniq, day_index = np.unique(days, return_inverse=True)
    years, months = np.array([d[:4] for d in uniq]), np.array([d[:7] for d in uniq])
    by = (groups(years), groups(months))
    counts = np.bincount(day_index, minlength=len(uniq))
    runs = draws(n, seed, utilization)
    out = {}
    for design in designs:
        acc = {}
        for p in runs:
            p = bp.for_location(p, tdb, rh)
            h = bp.hourly(tdb, twb, rh, design, p)
            for name in ("withdrawn", "consumed", "returned"):
                s = daily_stats(day_index, len(uniq), years, h[name], gwh, months if name != "returned" else None, by)
                for stat, v in s.items():
                    acc.setdefault(f"{name}_{stat}", []).append(v)
            day_mw = np.bincount(day_index, weights=h["electricity"], minlength=len(uniq)) / counts * gwh / 1000.0
            acc.setdefault("power_mw_avg", []).append(float(h["electricity"].mean()) * gwh / 1000.0)
            acc.setdefault("power_mw_peak_day_1in10", []).append(float(np.quantile([day_mw[g].max() for g in by[0]], 0.9)))
            acc.setdefault("fuel_mw_avg", []).append(float(h["fuel"].mean()) * gwh / 1000.0)
            made = bp.CELLS_PER_HOUR * p["utilization"]
            acc.setdefault("site_kwh_per_kwh", []).append(float((h["electricity"] + h["fuel"]).mean()) / made)
            acc.setdefault("withdrawn_l_per_kwh", []).append(float(h["withdrawn"].mean()) * bp.L_GAL / made)
            acc.setdefault("consumed_l_per_kwh", []).append(float(h["consumed"].mean()) * bp.L_GAL / made)
            acc.setdefault("utilization", []).append(p["utilization"])
        out[design] = {k: {"p10": float(np.quantile(v[:-1], 0.1)), "p50": float(np.quantile(v[:-1], 0.5)), "p90": float(np.quantile(v[:-1], 0.9)),
                           "central": float(v[-1])} for k, v in acc.items()}
    return out
