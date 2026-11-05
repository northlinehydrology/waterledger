"""Screening hydrology for a site (numpy and the standard library only).

Stormwater: design-storm runoff depth with the SCS (NRCS) curve number method, for land before and after development.
Groundwater: drawdown around a pumping well (Theis 1935) and the share of pumping taken from a nearby stream (Glover and
Balmer 1954). Screening level: volumes and analytical solutions, not routed hydrographs or numerical groundwater models.
"""
import math

import numpy as np

# Curve numbers for hydrologic soil group B (NRCS TR-55 Table 2-2): before, row crops, straight row, good condition (78; poor is 81, meadow 58);
# after, lawn, the midpoint of open space in good and fair condition (61, 69) [estimate]; pavement
CN_PRE_PERV, CN_POST_PERV, CN_IMP = 78, 65, 98


def scs_runoff_in(p_in, cn):
    """Runoff depth (inches) from a storm of `p_in` inches on land with curve number `cn` (NRCS TR-55, initial abstraction
    0.2 S)."""
    s = 1000 / cn - 10
    ia = 0.2 * s
    return 0.0 if p_in <= ia else (p_in - ia) ** 2 / (p_in + 0.8 * s)


def composite_runoff_in(p_in, impervious, cn_pervious, cn_impervious=CN_IMP):
    """Runoff depth (inches) from a site that is `impervious` (0-1) roofs and paving and the rest pervious, each computed
    separately and area-weighted (rather than one composite curve number, which understates runoff from paving)."""
    return impervious * scs_runoff_in(p_in, cn_impervious) + (1 - impervious) * scs_runoff_in(p_in, cn_pervious)


def well_function(u):
    """The Theis well function W(u), the exponential integral E1(u): a series below 1, a rational approximation above
    (Abramowitz and Stegun 5.1.56)."""
    if u <= 1:
        s, term = -0.5772156649 - math.log(u), 1.0
        for k in range(1, 40):
            term *= -u / k
            s -= term / k
        return s
    a = [8.5733287401, 18.0590169730, 8.6347608925, 0.2677737343]
    b = [9.5733223454, 25.6329561486, 21.0996530827, 3.9584969228]
    num = u ** 4 + a[0] * u ** 3 + a[1] * u ** 2 + a[2] * u + a[3]
    den = u ** 4 + b[0] * u ** 3 + b[1] * u ** 2 + b[2] * u + b[3]
    return num / den * math.exp(-u) / u


def theis_drawdown(q, transmissivity, storativity, r, t):
    """Drawdown at distance `r` after pumping at rate `q` for time `t` (Theis 1935), in consistent units: for example q in
    ft3/day, transmissivity in ft2/day, r in ft and t in days give feet."""
    return q / (4 * math.pi * transmissivity) * well_function(r * r * storativity / (4 * transmissivity * t))


def erfc(x):
    """The complementary error function on arrays (numpy has none): the Maclaurin series of erf below 1.5 and the Laplace continued
    fraction above, within 1e-13 of math.erfc wherever the result is not subnormal."""
    x = np.asarray(x, dtype=float)
    a = np.abs(x)
    out = np.empty_like(a)
    near = a < 1.5
    xs = a[near]
    term, total = xs.copy(), xs.copy()
    for n in range(1, 60):                      # erf(x) = 2/sqrt(pi) sum (-1)^n x^(2n+1) / (n! (2n+1))
        term = term * -(xs * xs) / n
        total += term / (2 * n + 1)
    out[near] = 1.0 - 2.0 / math.sqrt(math.pi) * total
    xl = a[~near]
    f = xl.copy()
    for k in range(200, 0, -1):                 # erfc(x) = exp(-x^2) / sqrt(pi) / (x + (1/2) / (x + 1 / (x + (3/2) / (x + ...))))
        f = xl + (k / 2) / f
    with np.errstate(invalid="ignore"):
        out[~near] = np.where(np.isinf(xl), 0.0, np.exp(-xl * xl) / math.sqrt(math.pi) / f)
    return np.where(x < 0, 2.0 - out, out)


def stream_depletion(distance, transmissivity, storativity, t):
    """Share (0-1) of a well's pumping that comes from a fully penetrating stream at `distance` after time `t` (Glover and
    Balmer 1954): erfc(sqrt(d^2 S / 4 T t)). Consistent units, as for theis_drawdown. Any argument can be an array (a well's
    response at every step of a run in one call), and the result has their broadcast shape; scalars give a float. At t = 0
    the share is 0."""
    t = np.asarray(t, dtype=float)
    with np.errstate(divide="ignore"):
        u = np.sqrt(np.asarray(distance, dtype=float) ** 2 * storativity / (4 * np.asarray(transmissivity, dtype=float) * t))
    share = erfc(u)
    return float(share) if share.ndim == 0 else share
