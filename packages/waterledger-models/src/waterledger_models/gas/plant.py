"""The gas plant Monte Carlo at one location, on the shared runner (waterledger_models.runs; design 0014): every draw's hours through
physics.hourly, then the runner's daily statistics. A standalone plant runs at a capacity factor (its demand a flat share of its available
capacity); in a supply scenario the plant serves another user's hourly load instead (design 0014, decision 7).

A plant draws no water at the grid's power plants for its own use (its auxiliary load is its own output): that is its stated exception to
design 0010's standard treatment (item 4), so `grid` is not taken.
"""

from waterledger_models import heat_rejection as hr
from waterledger_models import runs
from waterledger_models.gas import physics as gp

DRAWS = 400


def draws(technology, design, n=DRAWS, seed=7, nox="dln", settings=None):
    """The Monte Carlo draws, then the central run last: [{name: value}]. settings fixes parameters in every run."""
    r = gp.ranges(technology, design, nox)
    settings = settings or {}
    unknown = set(settings) - set(r)
    if unknown:
        raise ValueError(f"unknown settings: {sorted(unknown)}")
    lh = hr.latin_hypercube(r, n, seed)
    out = [{k: float(v[i]) for k, v in lh.items()} for i in range(n)] + [gp.central_parameters(technology, design, nox)]
    return [{**p, **settings} for p in out]


def run_location(times, temps, rhs, technology, design, units, unit_mw, capacity_factor=1.0, n=DRAWS, seed=7, nox="dln", inlet_cooling=False,
                 outages=False, water_temps=None, settings=None):
    """Monte Carlo for one gas plant at one location: `units` identical units of `unit_mw` net MW at ISO, asked for `capacity_factor` of its ISO
    rating every hour. Results as runs.run_location gives them for the plant's water (MGD) and its own electricity (the auxiliary load, MW), with
    the plant's own measures: net_mw_avg, unserved_mw_avg, fuel_mw_avg, heat_rate_avg (Btu/kWh, HHV, fuel over net) and water per MWh net,
    withdrawn_gal_per_mwh and consumed_gal_per_mwh. outages: draw each hour's units up at the sampled availability (physics.outages)."""
    model = _GasRuns(technology, design, units, unit_mw, capacity_factor, n, seed, nox, inlet_cooling, outages, water_temps, settings)
    return runs.run_location(model, times, temps, rhs)


class _GasRuns:
    """The gas plant's part of the shared runner: its draws and each draw's hours."""

    def __init__(self, technology, design, units, unit_mw, capacity_factor, n, seed, nox, inlet_cooling, outages, water_temps, settings):
        self.technology, self.design, self.units, self.unit_mw, self.cf = technology, design, units, unit_mw, capacity_factor
        self.n, self.seed, self.nox, self.inlet_cooling, self.outages, self.settings = n, seed, nox, inlet_cooling, outages, settings
        self.water_temps = water_temps
        self.designs = (design,)

    def draws(self):
        return draws(self.technology, self.design, self.n, self.seed, self.nox, self.settings)

    def setup(self, times, tdb, twb, rh):
        from waterledger_models.battery.plant import lake_hours
        self.tdb, self.twb, self.rh = tdb, twb, rh
        self.water_t = None if self.water_temps is None else lake_hours(times, self.water_temps)
        self.i = 0

    def run(self, design, p):
        p = hr.for_location(p, self.tdb)
        up = gp.outages(self.units, p["availability"], len(self.tdb), self.seed + self.i) if self.outages else None
        self.i += 1
        demand = self.cf * self.units * self.unit_mw
        h = gp.hourly(demand, self.tdb, self.twb, self.rh, self.technology, design, p, self.units, self.unit_mw, self.inlet_cooling, self.water_t, up)
        net = float(h["served"].sum())
        per_mwh = lambda x: float(x.sum()) / net if net > 0 else 0.0
        return runs.Hours(water={name: (h[name], 1.0) for name in ("withdrawn", "consumed", "returned", "to_sewer", "to_source")},
                          mw=h["aux"], utilization=float(self.cf),
                          extras={"net_mw_avg": float(h["served"].mean()), "unserved_mw_avg": float(h["unserved"].mean()),
                                  "fuel_mw_avg": float(h["fuel"].mean()), "heat_rate_avg": per_mwh(h["fuel"]) * gp.KWH_BTU,
                                  "withdrawn_gal_per_mwh": per_mwh(h["withdrawn"]), "consumed_gal_per_mwh": per_mwh(h["consumed"])})
