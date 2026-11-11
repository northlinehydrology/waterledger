"""Power supply scenarios (design 0014, step 4): what serves a water user's hourly electricity, and the water that takes, as the shared runner's
extra (waterledger_models.runs). Every plant is hypothetical: a technology, a size, a cooling design; none stands for a real project.

A scenario is resources (new PV, new wind, a new gas plant) and a residual rule (decision 1). For each draw, at the run's load and again at the
peak day's, hour by hour (decision 4):
  1. PV and wind serve the load first; what they make above it is surplus, exported, with no water credit (its MWh are reported).
  2. A gas plant serves a firm MW if it has one, otherwise the rest of the load, up to its units available (outages drawn per draw).
  3. What remains goes by the residual rule: "grid" (the default, decision 5) to the grid, whose water is the runner's grid.RunWater; "gas" or
     "none" (islanded) to nothing: unserved, reported, never filled.
The balance closes every hour: load = renewables served + gas + grid + unserved, and generation = served + surplus (tests/test_scenarios.py).

Sizing is done once, from the user's central draw (decision 6): size(model, ...) gives each scenario's PV and wind MW for a share of the annual
MWh, and a gas plant's units, N + k at the place's 0.4% design dry-bulb for the 1-in-10-year highest hour at full capacity.

Results, every name prefixed supply_<scenario>_ (0014, "What each scenario reports"): the gas plant's water roles with the runner's daily
statistics (gas_withdrawn_avg, ..._peak_1in10, ...); the residual's grid_<BA>_<kind>_avg and _peak_1in10; and per draw share_pv, share_wind,
share_gas, share_grid, annual_matching, unserved_mwh_annual, unserved_hours_annual, unserved_mw_max, unserved_run_max_hours, surplus_mwh_annual, pv_mwh_annual,
wind_mwh_annual, pv_cf, wind_cf, gas_fuel_mw_avg, gas_capacity_factor, gas_withdrawn_gal_per_mwh, gas_consumed_gal_per_mwh, pv_washing_mgd,
and local_withdrawn_avg and local_consumed_avg (MGD: the gas plant and the panel washing, the water on the campus's own source or system,
decision 8). Construction water is a one-time total by size, reported apart (decision 11), and comes with renewables' land and runoff.
"""
from dataclasses import dataclass

import numpy as np

from waterledger_models import heat_rejection as hr
from waterledger_models import runs
from waterledger_models.gas import physics as gp
from waterledger_models.supply import pv, wind

RESIDUALS = ("grid", "gas", "none")
HOURS_A_YEAR = 8766.0
# Panel washing, gal per MWh: 0-5 where operators do not wash (Macknick et al. 2012, Table 1; Meldrum et al. 2013, Table 11), more in dry
# regions; a setting by region [A].
WASHING = {"pv_washing": (0.0, 5.0)}


@dataclass
class Gas:
    """A gas plant resource: technology and design (gas.physics.DESIGNS), unit size, and units (None: sized N + k)."""
    technology: str = "cc"
    design: str = "towers"
    unit_mw: float = 300.0
    units: int | None = None
    k: int = 1
    firm_mw: float | None = None         # grid-parallel: serves this much of the load each hour, the residual takes the rest
    nox: str = "dln"
    inlet_cooling: bool = False
    outages: bool = True
    supply: str = "utility"              # where its water comes from: sets where its wastewater goes unless discharge is given (decision 10)
    discharge: str | None = None


@dataclass
class Scenario:
    """Resources and a residual rule. PV and wind by MW (AC for PV, nameplate for wind) or by share of the user's annual MWh."""
    residual: str = "grid"
    pv_mw: float | None = None
    pv_share: float | None = None
    pv_mount: str = "tracking"
    wind_mw: float | None = None
    wind_share: float | None = None
    gas: Gas | None = None


def _lhs(ranges, n, seed):
    """n Latin hypercube draws and the central values last, as the types' draws are."""
    d = hr.latin_hypercube(ranges, n, seed)
    return [{k: float(v[i]) for k, v in d.items()} for i in range(n)] + [{k: (a + b) / 2 for k, (a, b) in ranges.items()}]


def _year_max_quantile(x, years):
    return float(np.quantile([x[years == y].max() for y in np.unique(years)], 0.9))


def size(model, times, temps, rhs, scenarios, design, supply_weather, lat, lon):
    """Each scenario with its sizes fixed from the user's central draw (decision 6): PV and wind MW for their share of the annual MWh at central
    parameters, and a gas plant's units, N + k, N carrying the 1-in-10-year highest hour at full capacity at the place's 0.4% design dry-bulb."""
    tdb, rh = np.asarray(temps, float), np.asarray(rhs, float)
    twb = hr.wet_bulb(tdb, rh)
    model.setup(times, tdb, twb, rh)
    h = model.run(design, model.draws()[-1])
    annual_mwh = float(h.mw.mean()) * HOURS_A_YEAR
    full = h.mw if h.mw_full is None else h.mw_full
    peak = _year_max_quantile(full, np.array([t[:4] for t in times]))
    utc, ghi, beam, u, v = supply_weather
    out = {}
    for name, sc in scenarios.items():
        sc = Scenario(**vars(sc))
        if sc.pv_share is not None:
            g = pv.geometry(utc, lat, lon, sc.pv_mount)
            sc.pv_mw = sc.pv_share * annual_mwh / (float(pv.output(g, ghi, beam, tdb, np.hypot(u, v), _lhs(pv.RANGES, 1, 0)[-1]).mean()) * HOURS_A_YEAR)
        if sc.wind_share is not None:
            sc.wind_mw = sc.wind_share * annual_mwh / (float(wind.hourly(u, v, _lhs(wind.RANGES, 1, 0)[-1]).mean()) * HOURS_A_YEAR)
        if sc.gas is not None and sc.gas.units is None:
            gas = Gas(**vars(sc.gas))
            p = hr.for_location(gp.central_parameters(gas.technology, gas.design, gas.nox), tdb)
            t = np.array([p["design_db"]])
            cap = gp.hourly(1e9, t, hr.wet_bulb(t, np.array([40.0])), np.array([40.0]), gas.technology, gas.design, p, 1, gas.unit_mw,
                            gas.inlet_cooling, water_t=np.array([10.0]) if gas.design == "lake" else None)["capacity"][0]
            need = (gas.firm_mw if gas.firm_mw is not None else peak)
            gas.units = int(np.ceil(need / cap - 1e-9)) + gas.k
            sc.gas = gas
        out[name] = sc
    return out


def longest_run(flags):
    """The longest run of consecutive True hours, as a float (0 with none)."""
    f = np.r_[False, np.asarray(flags, bool), False]
    edges = np.flatnonzero(f[1:] != f[:-1])
    return float((edges[1::2] - edges[::2]).max()) if len(edges) else 0.0


class Supply:
    """The runner's extra for supply scenarios. scenarios: {name: Scenario} with sizes fixed (size()); supply_weather: (utc, ghi,
    beam_horizontal, u100, v100) on the runner's hours (waterledger_data.era5.supply); lat, lon: the place's; n and seed: the supply's own draws,
    n as the user's; water_temps: the lake's daily temperatures for a lake-cooled gas plant."""

    def __init__(self, scenarios, supply_weather, lat, lon, n, seed=11, water_temps=None):
        for name, sc in scenarios.items():
            if sc.residual not in RESIDUALS:
                raise ValueError(f"{name}: residual must be one of {RESIDUALS}")
            if (sc.pv_mw is None and sc.pv_share is not None) or (sc.wind_mw is None and sc.wind_share is not None) or (sc.gas and sc.gas.units is None):
                raise ValueError(f"{name}: size the scenario first (supply.scenario.size)")
            if sc.residual == "gas" and sc.gas is None:
                raise ValueError(f"{name}: a gas residual needs a gas resource")
        self.scenarios, self.lat, self.lon, self.water_temps = scenarios, lat, lon, water_temps
        self.utc, self.ghi, self.beam, self.u, self.v = (np.asarray(x) for x in supply_weather)
        self.pv_draws = _lhs({**pv.RANGES, **WASHING}, n, seed)
        self.wind_draws = _lhs(wind.RANGES, n, seed + 1)
        self.gas_draws = {name: _lhs(gp.ranges(sc.gas.technology, sc.gas.design, sc.gas.nox), n, seed + 2) for name, sc in scenarios.items() if sc.gas}
        self.seed = seed

    def setup(self, times, tdb, twb, rh):
        if len(times) != len(self.utc):
            raise ValueError("the supply weather must be on the runner's hours (waterledger_data.era5.supply)")
        from waterledger_models.battery.plant import lake_hours
        self.tdb, self.twb, self.rh = tdb, twb, rh
        self.years = len(times) / HOURS_A_YEAR
        self.ndays = len(times) / 24.0
        self.water_t = None if self.water_temps is None else lake_hours(times, self.water_temps)
        mounts = {sc.pv_mount for sc in self.scenarios.values() if sc.pv_mw}
        self.geometry = {m: pv.geometry(self.utc, self.lat, self.lon, m) for m in mounts}
        self.wind_100m = np.hypot(self.u, self.v)

    def _dispatch(self, sc, name, load, pv_prof, wind_prof, i):
        gen_pv = (sc.pv_mw or 0.0) * pv_prof * np.ones_like(load)
        gen_wind = (sc.wind_mw or 0.0) * wind_prof * np.ones_like(load)
        gen = gen_pv + gen_wind
        renew = np.minimum(gen, load)
        rest = load - renew
        gh = None
        if sc.gas is not None:
            g = sc.gas
            demand = np.minimum(rest, g.firm_mw) if g.firm_mw is not None else rest
            p = hr.for_location(self.gas_draws[name][i], self.tdb)
            up = gp.outages(g.units, p["availability"], len(load), self.seed + 1000 * i) if g.outages else None
            gh = gp.hourly(demand, self.tdb, self.twb, self.rh, g.technology, g.design, p, g.units, g.unit_mw, g.inlet_cooling, self.water_t, up,
                           g.discharge or gp.default_discharge(g.technology, g.design, g.supply))
            rest = rest - gh["served"]
        grid = rest if sc.residual == "grid" else 0.0 * rest
        unserved = rest - grid
        share = np.divide(gen_pv, gen, out=np.zeros_like(gen), where=gen > 0)
        return {"load": load, "gen_pv": gen_pv, "gen_wind": gen_wind, "renew": renew, "renew_pv": renew * share, "renew_wind": renew * (1 - share),
                "surplus": gen - renew, "gas": gh, "grid": grid, "unserved": unserved}

    def __call__(self, design, p, hours, i):
        pv_p, wind_p = self.pv_draws[i], self.wind_draws[i]
        profiles = {m: pv.output(g, self.ghi, self.beam, self.tdb, self.wind_100m, pv_p) for m, g in self.geometry.items()}
        wind_prof = wind.hourly(self.u, self.v, wind_p)
        out = runs.Supplied(peak={}, grid_mw_peak={})
        for name, sc in self.scenarios.items():
            pre = f"supply_{name}_"
            pv_prof = profiles.get(sc.pv_mount, 0.0)
            d = self._dispatch(sc, name, hours.mw, pv_prof, wind_prof, i)
            dp = self._dispatch(sc, name, hours.mw if hours.mw_peak is None else hours.mw_peak, pv_prof, wind_prof, i)
            if sc.residual == "grid":                    # the residual's water at the grid's plants, through the runner's grid.RunWater
                out.grid_mw[pre[:-1]], out.grid_mw_peak[pre[:-1]] = d["grid"], dp["grid"]
            total = float(d["load"].sum())
            frac = lambda x: float(np.sum(x)) / total if total > 0 else 0.0
            washing = d["gen_pv"] * pv_p["pv_washing"]                    # gallons each hour
            s = {"share_pv": frac(d["renew_pv"]), "share_wind": frac(d["renew_wind"]), "share_grid": frac(d["grid"]),
                 "share_gas": frac(d["gas"]["served"]) if d["gas"] is not None else 0.0,
                 "annual_matching": frac(d["gen_pv"] + d["gen_wind"]),
                 "unserved_mwh_annual": float(d["unserved"].sum()) / self.years,
                 "unserved_hours_annual": float((d["unserved"] > 1e-9).sum()) / self.years, "unserved_mw_max": float(d["unserved"].max()),
                 "unserved_run_max_hours": longest_run(d["unserved"] > 1e-9),
                 "surplus_mwh_annual": float(d["surplus"].sum()) / self.years,
                 "pv_mwh_annual": float(d["gen_pv"].sum()) / self.years, "wind_mwh_annual": float(d["gen_wind"].sum()) / self.years,
                 "pv_cf": float(np.mean(pv_prof)) if sc.pv_mw else 0.0, "wind_cf": float(wind_prof.mean()) if sc.wind_mw else 0.0,
                 "pv_washing_mgd": float(washing.sum()) / self.ndays / 1e6}
            local_w, local_c = s["pv_washing_mgd"], s["pv_washing_mgd"]
            if d["gas"] is not None:
                gh, ghp, g = d["gas"], dp["gas"], sc.gas
                for role in ("withdrawn", "consumed", "returned", "to_sewer", "to_source", "to_stream"):
                    out.water[f"{pre}gas_{role}"] = (gh[role], 1.0)
                    out.peak[f"{pre}gas_{role}"] = (ghp[role], 1.0)
                served = float(gh["served"].sum())
                s.update({"gas_fuel_mw_avg": float(gh["fuel"].mean()), "gas_capacity_factor": float(gh["served"].mean()) / (g.units * g.unit_mw),
                          "gas_withdrawn_gal_per_mwh": float(gh["withdrawn"].sum()) / served if served > 0 else 0.0,
                          "gas_consumed_gal_per_mwh": float(gh["consumed"].sum()) / served if served > 0 else 0.0})
                local_w += float(gh["withdrawn"].sum()) / self.ndays / 1e6
                local_c += float(gh["consumed"].sum()) / self.ndays / 1e6
            s.update({"local_withdrawn_avg": local_w, "local_consumed_avg": local_c})
            out.scalars.update({pre + k: v for k, v in s.items()})
        return out
