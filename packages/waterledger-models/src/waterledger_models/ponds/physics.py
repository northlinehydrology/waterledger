"""A cooling pond, step by step (design 0024, part 2): a built pond a plant circulates, its heat leaving at the surface. What the pond held
the step before decides its water use, so it keeps state: its volume, its temperature and the dissolved mass in it.

The pond is well mixed. Each step:
- **Heat:** the plant's heat goes in; at the surface the pond absorbs shortwave and longwave and loses longwave, evaporation and conduction.
  Evaporation and conduction share Brady, Graves and Geyer's (1969) wind function for cooling ponds, f = 9.2 + 0.46 U2^2 W m-2 mmHg-1 with
  U2 the wind at 2 m (as quoted by Edinger et al. 1974 and the CE-QUAL-W2 manual), conduction through Bowen's ratio. The step is solved
  implicitly in the new temperature (Newton, bisection as a fallback), so it is stable at hourly or daily steps and the heat closes with
  every flux at the new temperature.
- **Water:** makeup (the withdrawal) brings the pond back to its operating volume after evaporation, seepage and blowdown, less the rain on
  it. Blowdown holds the cycles of concentration (blowdown + seepage = evaporation / (cycles - 1)); evaporation leaves its dissolved mass
  behind. Under a withdrawal limit, blowdown is cut first and then the pond draws down. Water above the operating volume spills.
- **Mass:** each constituent is mixed through the pond; what leaves (blowdown, spill, seepage) leaves at the new concentration.
- **A shadow pond** with no plant heat, at the same volume on the same weather, gives the evaporation the pond would have had anyway; the
  difference is the plant's forced evaporation (as USGS reports it for cooling ponds, Diehl and Harris 2014).

[A] marks assumptions, listed in POND_PARAMETERS with their defaults.
"""
import math

from waterledger_models.once_through import _es

RHO, CP, LV = 1000.0, 4186.0, 2.45e6       # kg m-3, J kg-1 K-1, J kg-1 (once_through's)
SIGMA = 5.670374419e-8                      # W m-2 K-4
MMHG_PER_HPA = 1.0 / 1.333224
T_MIN, T_MAX = 0.0, 100.0                   # the solve's bounds, C; ice isn't modelled: the pond is held at 0 C and the heat that takes is reported

# Defaults [A], each settable in a component's parameters.
POND_PARAMETERS = {
    "albedo": 0.06,                 # water's shortwave reflectance, a daily mean [A]
    "emissivity": 0.97,             # water's longwave emissivity and absorptance [A]
    "coc": 4.0,                     # cycles of concentration the operator holds [A]
    "seepage_mm_day": 1.0,          # loss through the bed, mm a day over the pond's area [A]
    "min_volume_share": 0.3,        # below this share of the operating volume the plant can't draw from the pond and its heat isn't taken [A]
    "max_supply_c": 35.0,           # the plant's highest workable supply temperature, C: hours above it are reported [A]
    "area_exponent": 2.0 / 3.0,     # area = operating area x (volume / operating volume) ^ this: a bowl of the same shape at every level [A]
    "wind_height_m": 10.0,          # height of the wind given (AORC and NWM give 10 m), taken to 2 m by a 1/7 power law [A]
}


def wind_function(u2):
    """Brady, Graves and Geyer (1969): W m-2 per hPa of vapor pressure difference, for a wind of u2 m s-1 at 2 m."""
    return (9.2 + 0.46 * u2 * u2) * MMHG_PER_HPA


def surface(t, air, ea, pressure_hpa, sw, lw, u2, p):
    """The surface's heat terms at pond temperature t, W m-2: (absorbed shortwave, absorbed longwave, emitted longwave, evaporation,
    conduction), the last three leaving. Evaporation isn't let below zero (condensation onto the pond is left out [A])."""
    f = wind_function(u2)
    evap = max(f * (_es(t) - ea), 0.0)
    cond = f * 0.00061 * pressure_hpa * (t - air)          # Bowen (1926): 0.61 P / 1000 hPa per C
    return (1.0 - p["albedo"]) * sw, p["emissivity"] * lw, p["emissivity"] * SIGMA * (t + 273.15) ** 4, evap, cond


def area(volume, p):
    """Surface area at a volume, m2."""
    return p["area_m2"] * (max(volume, 0.0) / p["volume_m3"]) ** p["area_exponent"]


def _water(evap_m3s, rain_m3s, volume, dt, cap, p):
    """Makeup, blowdown and seepage for a step with this evaporation, m3 s-1: (makeup, blowdown, seepage, wanted makeup)."""
    a = area(volume, p)
    seep = a * p["seepage_mm_day"] / 1000.0 / 86400.0
    blow = max(evap_m3s / (p["coc"] - 1.0) - seep, 0.0)
    want = max((p["volume_m3"] - volume) / dt + evap_m3s + blow + seep - rain_m3s, 0.0)
    makeup = min(want, cap)
    if makeup < want:                    # under a limit, blowdown goes first, then storage
        blow = max(blow - (want - makeup), 0.0)
    return makeup, blow, seep, want


def step(s, w, heat_w, cap, dt, p):
    """One step of the pond.

    s     state: volume (m3), temperature (C), mass {constituent: kg}
    w     the step's weather and water: air (C), ea (hPa), pressure_hpa, sw and lw (W m-2 down), u2 (m s-1 at 2 m), rain (mm s-1),
          makeup_c (the makeup's temperature, C), conc {constituent: kg m-3 in the makeup}
    heat_w  the plant's heat, W; cap  the most makeup allowed, m3 s-1 (infinity for none)
    Returns (new state, fluxes): every flow in m3 s-1, heat in W, mass in kg s-1, plus the terms the heat and water balances close with.
    """
    v0, t0 = s["volume"], s["temperature"]
    a = area(v0, p)
    rain = a * w["rain"] / 1000.0
    running = v0 >= p["min_volume_share"] * p["volume_m3"]
    q = heat_w if running else 0.0

    def terms(t):
        sw, lw, out, ev, cond = surface(t, w["air"], w["ea"], w["pressure_hpa"], w["sw"], w["lw"], w["u2"], p)
        evap = a * ev / (LV * RHO)
        makeup, blow, seep, want = _water(evap, rain, v0, dt, cap, p)
        net = a * (sw + lw - out - ev - cond)
        advected = RHO * CP * (makeup * (w["makeup_c"] - t) + rain * (w["air"] - t))
        return net, advected, evap, makeup, blow, seep, want, (sw, lw, out, ev, cond)

    def residual(t):
        net, advected = terms(t)[:2]
        return RHO * CP * v0 * (t - t0) - dt * (q + net + advected)

    t = _solve(residual, t0)
    freeze = 0.0
    if t < T_MIN:                        # ice isn't modelled: held at 0 C, the heat that takes reported
        t = T_MIN
        freeze = residual(T_MIN) / dt    # W it takes to hold it there
    evap, makeup, blow, seep, want, parts = terms(t)[2:]
    v1 = v0 + (makeup + rain - evap - blow - seep) * dt
    spill = max(v1 - p["volume_m3"], 0.0) / dt
    v1 -= spill * dt
    if v1 <= 0.0:
        raise RuntimeError("the cooling pond ran dry: its makeup is limited too long for its size")
    out_flow = blow + spill + seep
    mass, mass_in, mass_out, ground_mass = {}, {}, {}, {}
    for k, m in s["mass"].items():
        c_in = w["conc"].get(k, 0.0)
        m1 = (m + makeup * c_in * dt) / (1.0 + out_flow * dt / v1)
        mass[k] = m1
        mass_in[k] = makeup * c_in
        mass_out[k] = out_flow * m1 / v1
        ground_mass[k] = seep * m1 / v1
    shadow = natural_evaporation(s, w, dt, p, a, rain)
    f = {
        "makeup": makeup, "makeup_wanted": want, "rain": rain, "evaporation": evap, "natural_evaporation": shadow["evaporation"],
        "blowdown": blow, "spill": spill, "seepage": seep, "volume": v1, "area": area(v1, p), "temperature": t,
        "heat_in": q, "heat_unremoved": heat_w - q, "running": running,
        "shortwave": a * parts[0], "longwave_in": a * parts[1], "longwave_out": a * parts[2], "evaporation_heat": a * parts[3],
        "conduction": a * parts[4], "freeze_heat": freeze,
        "heat_in_water": RHO * CP * (makeup * w["makeup_c"] + rain * w["air"]),        # enthalpy above 0 C carried in and out by the water
        "heat_out_water": RHO * CP * (blow + spill + seep + evap) * t,
        "stored_heat_change": RHO * CP * (v1 * t - v0 * t0) / dt,
        "mass_in": mass_in, "mass_out": mass_out, "mass_to_ground": ground_mass,
    }
    return {"volume": v1, "temperature": t, "mass": mass, "natural_temperature": shadow["temperature"]}, f


def natural_evaporation(s, w, dt, p, a, rain):
    """The same pond with no plant heat, at the pond's own volume, its temperature carried as its own state: what would evaporate anyway."""
    t0 = s.get("natural_temperature", s["temperature"])
    v0 = s["volume"]

    def residual(t):
        sw, lw, out, ev, cond = surface(t, w["air"], w["ea"], w["pressure_hpa"], w["sw"], w["lw"], w["u2"], p)
        evap = a * ev / (LV * RHO)
        makeup = _water(evap, rain, v0, dt, math.inf, p)[0]
        return RHO * CP * v0 * (t - t0) - dt * (a * (sw + lw - out - ev - cond) + RHO * CP * (makeup * (w["makeup_c"] - t) + rain * (w["air"] - t)))

    t = max(_solve(residual, t0), T_MIN)
    ev = surface(t, w["air"], w["ea"], w["pressure_hpa"], w["sw"], w["lw"], w["u2"], p)[3]
    return {"temperature": t, "evaporation": a * ev / (LV * RHO)}


def _solve(f, x0, tol=1e-11):
    """The root of an increasing f: Newton from x0, bisection on [T_MIN - 60, T_MAX] where Newton doesn't settle."""
    x = x0
    for _ in range(50):
        fx = f(x)
        h = 1e-6 * max(1.0, abs(x))
        d = (f(x + h) - fx) / h
        if not d > 0:
            break
        nx = x - fx / d
        if not (T_MIN - 60.0 <= nx <= T_MAX):
            break
        if abs(nx - x) < tol:
            return nx
        x = nx
    lo, hi = T_MIN - 60.0, T_MAX
    if f(lo) > 0 or f(hi) < 0:
        raise RuntimeError("the cooling pond's heat balance has no temperature between -60 and 100 C")
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if f(mid) > 0:
            hi = mid
        else:
            lo = mid
        if hi - lo < tol:
            break
    return 0.5 * (lo + hi)


def wind_at_2m(u, height_m):
    """A wind measured at height_m taken to 2 m (1/7 power law) [A]."""
    return u * (2.0 / height_m) ** (1.0 / 7.0)
