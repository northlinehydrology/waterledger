"""A tailings pond, step by step (design 0025): a mine's impoundment and the mill's water circuit around it. The mill sends its tailings
to the impoundment as a slurry; the solids settle and keep water in their pores; the free water joins a pool on the deposit; the pool is
reclaimed back to the mill and the mill's makeup (the withdrawal) covers the rest. What the pool held the step before decides how much
makeup the mill needs, and the settled tailings fill the impoundment year by year, so the pond keeps state: the pool's volume, its
temperature, its dissolved mass, and the tailings' volume.

Each step:
- **The mill** needs the slurry's water (the solids rate x (1 - solids share) / solids share) and any water it uses otherwise, less the ore's
  moisture. Reclaim covers what it can (the pool above its lowest workable volume, at most the reclaim pumps' capacity); makeup covers the
  rest, up to a withdrawal limit. Where the two fall short, the mill processes only the ore its water allows (a physical limit, not an
  operating rule: rules belong in a scenario's schedules, Andrew, Nov 26); the shortfall is reported.
- **The tailings** settle at a dry density; their pores hold water (saturation x void ratio / specific gravity per tonne). That water is
  locked in the deposit and counted as consumption (Andrew, Nov 26). The deposit's volume grows by the solids over their dry density.
- **The pool** gains the slurry's free water, rain on it, runoff from the beach (the deposit's surface not under the pool) and from a
  catchment draining to it; it loses evaporation, seepage, reclaim and any release. Its area is its volume over a mean depth, at most the
  impoundment's surface at its fill.
- **Heat and evaporation:** the cooling pond's surface energy balance (ponds.physics) with no plant heat, solved implicitly in the pool's
  new temperature. Slurry, rain and runoff come in at the air's temperature [A].
- **Release:** water above the impoundment's operating capacity (less the tailings in it) is released to a stream. With zero discharge it
  is held and reported as freeboard used, and only water above the crest (operating capacity x (1 + freeboard share)) is released.
- **Mass:** each constituent is mixed through the pool. The mill's water mixes makeup and reclaim; the solids can release a mass per tonne
  [A]. What the tailings lock in their pores, and the mill's other use, leave at the mill water's concentration; seepage and release leave
  at the pool's new concentration.

[A] marks assumptions, listed in TAILINGS_PARAMETERS with their defaults.
"""
from waterledger_models.ponds import physics
from waterledger_models.ponds.physics import CP, LV, RHO, T_MIN

# Defaults [A], each settable in a component's parameters.
TAILINGS_PARAMETERS = {
    "solids_share": 0.35,           # solids by mass in the slurry the mill sends: conventional tailings, 0.25-0.40; thickened 0.50-0.70 [A]
    "dry_density_t_m3": 1.4,        # the settled deposit's dry density, t m-3 [A]
    "solids_gravity": 2.7,          # the solids' specific gravity [A]
    "saturation": 1.0,              # share of the deposit's pores holding water [A]
    "pool_depth_m": 2.0,            # the pool's mean depth: its area is its volume over this [A]
    "runoff_coefficient": 0.5,      # share of rain on the beach and the catchment that reaches the pool [A]
    "ore_moisture_m3_t": 0.0,       # water the ore brings to the mill, m3 per tonne of tailings solids [A]
    "mill_other_m3_t": 0.0,         # water the mill uses that doesn't go with the slurry (concentrate, dust, losses), m3 per tonne, consumed [A]
    "seepage_mm_day": 1.0,          # loss through the bed under the pool, mm a day over its area [A]
    "freeboard_share": 0.1,         # with zero discharge: the crest holds the operating capacity x (1 + this) [A]
    "area_exponent": 2.0 / 3.0,     # the impoundment's surface = its area at capacity x (fill / capacity) ^ this [A]
    "albedo": physics.POND_PARAMETERS["albedo"],
    "emissivity": physics.POND_PARAMETERS["emissivity"],
    "wind_height_m": physics.POND_PARAMETERS["wind_height_m"],
}
DISCHARGE = ("release", "zero")


def pore_water_m3_t(p):
    """Water the settled tailings lock in their pores, m3 per tonne of solids."""
    void_ratio = p["solids_gravity"] / p["dry_density_t_m3"] - 1.0
    return p["saturation"] * void_ratio / p["solids_gravity"]


def slurry_water_m3_t(p):
    """Water the slurry carries, m3 per tonne of solids."""
    return (1.0 - p["solids_share"]) / p["solids_share"]


def surface_area(fill, p):
    """The impoundment's surface at a fill (tailings + pool), m2."""
    return p["capacity_area_m2"] * (max(fill, 0.0) / p["capacity_m3"]) ** p["area_exponent"]


def pool_area(pool, tailings, p):
    """The pool's area, m2: its volume over its mean depth, at most the impoundment's surface."""
    return min(max(pool, 0.0) / p["pool_depth_m"], surface_area(tailings + pool, p))


def step(s, w, solids_t_s, cap, dt, p):
    """One step of the tailings pond and the mill's water.

    s     state: pool (m3), tailings (m3), temperature (C), mass {constituent: kg in the pool}
    w     the step's weather and water: air (C), ea (hPa), pressure_hpa, sw and lw (W m-2 down), u2 (m s-1 at 2 m), rain (mm s-1),
          conc {constituent: kg m-3 in the makeup}, release {constituent: kg per tonne of solids}
    solids_t_s  the mill's tailings solids, t s-1, at full throughput; cap  the most makeup allowed, m3 s-1 (infinity for none)
    Returns (new state, fluxes): flows in m3 s-1, heat in W, mass in kg s-1, plus the terms the balances close with.
    """
    v0, d0, t0 = s["pool"], s["tailings"], s["temperature"]
    per_t = slurry_water_m3_t(p) + p["mill_other_m3_t"] - p["ore_moisture_m3_t"]
    demand = solids_t_s * per_t
    reclaim = min(demand, max(v0 - p["min_pool_m3"], 0.0) / dt, p["reclaim_max_m3_s"])
    makeup = min(demand - reclaim, cap)
    share = 1.0 if demand <= 0.0 else min((reclaim + makeup) / demand, 1.0)
    solids = solids_t_s * share                               # what the mill can process on the water it has
    slurry = solids * slurry_water_m3_t(p)
    locked = solids * pore_water_m3_t(p)
    other = solids * p["mill_other_m3_t"]
    ore = solids * p["ore_moisture_m3_t"]
    free = slurry - locked

    surf = surface_area(d0 + v0, p)
    a = pool_area(v0, d0, p)
    rain_pool = a * w["rain"] / 1000.0
    runoff = ((surf - a) + p["catchment_m2"]) * w["rain"] / 1000.0 * p["runoff_coefficient"]
    seep = a * p["seepage_mm_day"] / 1000.0 / 86400.0
    inflow = free + rain_pool + runoff                        # what comes in at the air's temperature [A]

    def terms(t):
        return physics.surface(t, w["air"], w["ea"], w["pressure_hpa"], w["sw"], w["lw"], w["u2"], p)

    def residual(t):
        sw, lw, out, ev, cond = terms(t)
        return RHO * CP * v0 * (t - t0) - dt * (a * (sw + lw - out - ev - cond) + RHO * CP * inflow * (w["air"] - t))

    t = physics._solve(residual, t0)
    freeze = 0.0
    if t < T_MIN:                        # ice isn't modelled: held at 0 C, the heat that takes reported
        t = T_MIN
        freeze = residual(T_MIN) / dt
    parts = terms(t)
    evap = a * parts[3] / (LV * RHO)

    d1 = d0 + solids / p["dry_density_t_m3"] * dt
    if d1 >= p["capacity_m3"]:
        raise RuntimeError("the tailings impoundment is full: its tailings have reached its operating capacity")
    v1 = v0 + (inflow - evap - seep - reclaim) * dt
    room = p["capacity_m3"] - d1
    crest = p["capacity_m3"] * (1.0 + p["freeboard_share"]) - d1 if p["discharge"] == "zero" else room
    release = max(v1 - crest, 0.0) / dt
    v1 -= release * dt
    if v1 <= 0.0:
        raise RuntimeError("the tailings pool ran dry: its losses and reclaim outran its inflow for its size")
    freeboard_used = max(v1 - room, 0.0)

    mill_in = makeup + reclaim + ore                            # = slurry + other
    mass, mass_in, mass_out, ground_mass, locked_mass = {}, {}, {}, {}, {}
    for k, m in s["mass"].items():
        c0 = m / v0
        c_in = w["conc"].get(k, 0.0)
        rel = solids * w["release"].get(k, 0.0)
        c_mill = (makeup * c_in + reclaim * c0 + rel) / mill_in if mill_in > 0 else 0.0
        m1 = (m + dt * (free * c_mill - reclaim * c0)) / (1.0 + (seep + release) * dt / v1)
        mass[k] = m1
        mass_in[k] = makeup * c_in + rel
        mass_out[k] = (seep + release) * m1 / v1
        ground_mass[k] = seep * m1 / v1
        locked_mass[k] = (locked + other) * c_mill
    f = {
        "demand": demand, "reclaim": reclaim, "makeup": makeup, "share": share, "unmet": demand * (1.0 - share), "solids": solids,
        "slurry": slurry, "locked": locked, "mill_other": other, "ore": ore, "free": free,
        "rain": rain_pool, "runoff": runoff, "evaporation": evap, "seepage": seep, "release": release, "freeboard_used": freeboard_used,
        "pool": v1, "tailings": d1, "area": pool_area(v1, d1, p), "temperature": t,
        "shortwave": a * parts[0], "longwave_in": a * parts[1], "longwave_out": a * parts[2], "evaporation_heat": a * parts[3],
        "conduction": a * parts[4], "freeze_heat": freeze,
        "heat_in_water": RHO * CP * inflow * w["air"],              # enthalpy above 0 C carried in and out by the water
        "heat_out_water": RHO * CP * (evap + seep + reclaim + release) * t,
        "stored_heat_change": RHO * CP * (v1 * t - v0 * t0) / dt,
        "mass_in": mass_in, "mass_out": mass_out, "mass_to_ground": ground_mass, "mass_locked": locked_mass,
    }
    return {"pool": v1, "tailings": d1, "temperature": t, "mass": mass}, f


def check(p):
    """Refuse parameters the step can't use."""
    if not 0.0 < p["solids_share"] < 1.0:
        raise ValueError("solids_share, solids by mass in the slurry, must be between 0 and 1")
    if not (p["dry_density_t_m3"] > 0 and p["solids_gravity"] > p["dry_density_t_m3"]):
        raise ValueError("dry_density_t_m3 must be positive and below solids_gravity (the deposit has pores)")
    if not 0.0 <= p["saturation"] <= 1.0:
        raise ValueError("saturation must be between 0 and 1")
    if pore_water_m3_t(p) > slurry_water_m3_t(p):
        raise ValueError("the tailings' pores hold more water than the slurry carries: raise the slurry's water or lower the saturation")
    if p["ore_moisture_m3_t"] > slurry_water_m3_t(p) + p["mill_other_m3_t"]:
        raise ValueError("ore_moisture_m3_t is more water than the mill uses")
    for k in ("pool_depth_m", "capacity_m3", "capacity_area_m2"):
        if not p[k] > 0:
            raise ValueError(f"{k} must be positive")
    if not 0.0 <= p["runoff_coefficient"] <= 1.0:
        raise ValueError("runoff_coefficient must be between 0 and 1")
    for k in ("mill_other_m3_t", "ore_moisture_m3_t", "seepage_mm_day", "freeboard_share", "catchment_m2", "min_pool_m3"):
        if p[k] < 0:
            raise ValueError(f"{k} can't be negative")
    if not p["reclaim_max_m3_s"] >= 0:
        raise ValueError("reclaim_max_m3_s can't be negative")
    if p["discharge"] not in DISCHARGE:
        raise ValueError(f"discharge must be one of {DISCHARGE}")
