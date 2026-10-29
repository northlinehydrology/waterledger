"""Screening hydrology for a site (numpy and the standard library only).

Stormwater: design-storm runoff depth with the SCS (NRCS) curve number method, for land before and after development.
Groundwater: drawdown around a pumping well (Theis 1935) and the share of pumping taken from a nearby stream (Glover and
Balmer 1954). Screening level: volumes and analytical solutions, not routed hydrographs or numerical groundwater models.
"""
import math

# Curve numbers for hydrologic soil group B [estimate; NRCS TR-55 Table 2-2]: row crops or meadow before, lawn after, pavement
CN_PRE_PERV, CN_POST_PERV, CN_IMP = 72, 65, 98


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


def stream_depletion(distance, transmissivity, storativity, t):
    """Share (0-1) of a well's pumping that comes from a fully penetrating stream at `distance` after time `t` (Glover and
    Balmer 1954): erfc(sqrt(d^2 S / 4 T t)). Consistent units, as for theis_drawdown."""
    return math.erfc(math.sqrt(distance * distance * storativity / (4 * transmissivity * t)))
