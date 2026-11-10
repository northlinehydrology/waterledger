"""Hourly output of a hypothetical onshore wind project, per MW of nameplate (design 0014).

ERA5's 100 m wind (the u and v components, instantaneous at the hour) is taken to hub height by a power law, through a reference turbine's power
curve, less plant losses:

  speed at hub     |(u, v)| x (hub / 100 m)^alpha, alpha 0.10-0.20 around the 1/7 of neutral air over open land [A]
  turbine          the IEA 3.4 MW reference turbine (130 m rotor, 110 m hub, IEC class IIIa; Bortolotti et al. 2019, NREL/TP-5000-73492),
                   its power curve as NREL's turbine-models library gives it (github.com/NREL/turbine-models, commit e9e4ccc,
                   data/Onshore/IEA_Reference_3.4MW_130.csv, BSD-3-Clause): 0 under 3 m/s and above the 25 m/s cut-out, linear between points
  losses           wakes, availability and electrical losses, 10-20% [A] (design 0014)
  resource         a factor on the speed until ERA5 is checked against output at the cells (0014, check 5) [A]

ERA5 is known to run low on hub-height wind over land and to miss the evening ramp by the hour (Davidson and Millstein 2022; Staffell and
Pfenninger 2016), so the resource factor is sampled, not fixed at 1, until that check is run.
"""
import numpy as np

HUB_M = 110.0
RATED_KW = 3370.0
SPEED = (3, 3.5392, 4.0485, 4.5267, 4.973, 5.3862, 5.7654, 6.1098, 6.4186, 6.6912, 6.9269, 7.1252, 7.2857, 7.408, 7.4919, 7.5371, 7.5435,
         7.5758, 7.6468, 7.7563, 7.9041, 8.0899, 8.3132, 8.5735, 8.8703, 9.203, 9.5707, 9.8127, 10.408, 10.8757, 11.3748, 11.9041, 12.4625,
         13.0487, 13.6615, 14.2995, 14.9612, 15.6452, 16.35, 17.074, 17.8155, 18.5731, 19.3448, 20.1292, 20.9244, 21.7286, 22.5401, 23.357,
         24.1776, 25)
POWER_KW = (51.6, 123.4, 213.2, 318.8, 436.0, 560.9, 688.9, 819.1, 949.7, 1075.9, 1193.7, 1299.2, 1389.0, 1460.1, 1510.2, 1537.7, 1541.7,
            1561.6, 1605.9, 1675.9, 1773.5, 1901.5, 2063.3, 2263.3, 2506.6, 2799.3, 3148.5, 3370.0, 3370.0, 3370.0, 3370.0, 3370.0, 3370.0,
            3370.0, 3370.0, 3370.0, 3370.0, 3370.0, 3370.0, 3370.0, 3370.0, 3370.0, 3370.0, 3370.0, 3370.0, 3370.0, 3370.0, 3370.0, 3370.0,
            3370.1)
CUT_OUT = 25.0
RANGES = {
    "alpha": (0.10, 0.20),       # shear exponent, 100 m to hub [A]
    "losses": (0.10, 0.20),      # wakes, availability, electrical [A]
    "resource": (0.95, 1.10),    # a factor on ERA5's speed until checked against output [A]
}


def power_curve(speed):
    """Turbine output as a share of its rating at hub-height wind speed, m/s."""
    s = np.asarray(speed, dtype=float)
    out = np.interp(s, SPEED, POWER_KW, left=0.0, right=0.0) / RATED_KW
    return np.where((s < SPEED[0]) | (s > CUT_OUT), 0.0, np.minimum(out, 1.0))


def hourly(u100, v100, p):
    """Output per MW of nameplate each hour (0-1) from ERA5's 100 m wind components, m/s. p: RANGES' parameters (scalars or (n, 1) arrays)."""
    speed = np.hypot(np.asarray(u100, float), np.asarray(v100, float)) * p["resource"] * (HUB_M / 100.0) ** p["alpha"]
    return power_curve(speed) * (1.0 - p["losses"])
