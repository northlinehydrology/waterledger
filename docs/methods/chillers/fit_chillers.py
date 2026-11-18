"""Fit the model's chiller form to ASHRAE 90.1's reference curves (designs 0015 and 0021).

The model's form, both chiller types:

    1/COP = loss + lift / (eta x T_evap)        T_evap = leaving chilled water - 2 C, in K

    air-cooled:    lift = air at the coil + 12 - T_evap
    water-cooled:  lift = entering condenser water + range + 2 - T_evap

The reference: ASHRAE 90.1-2016's default EIR-FT curves (COMNET 2017), as given in PNNL-26917, the 90.1-2016 Performance Rating
Method Reference Manual (Goel, Rosenberg and Eley, Sept 2017), Tables 80 (air-cooled) and 81 (water-cooled), each a biquadratic in
leaving chilled water and outdoor dry-bulb or entering condenser water, F, valid on 40-54 F water and 40-115 F air or 60-85 F condenser
water. At full available load (EIR-FPLR(1) = 1 within 0.3%), kW per kW of cooling is the rated value x EIR-FT, so COP = rated COP / EIR-FT.

Least squares on relative error of COP, over the curve's range (and for air the hours chillers run, 15-46 C), normalized to the
rating point. Run:  uv run python docs/methods/chillers/fit_chillers.py
"""
import numpy as np
from scipy.optimize import least_squares

F = lambda c: c * 9 / 5 + 32
C = lambda f: (f - 32) * 5 / 9

# PNNL-26917 Table 80 (air-cooled) and Table 81 (water-cooled): a, b, c, d, e, f in EIR = a + b t + c t^2 + d x + e x^2 + f t x, F
AIR = {"screw": (0.13545636, 0.02292946, -0.00016107, -0.00235396, 0.00012991, -0.00018685),
       "scroll": (0.99006553, -0.00584144, 0.00016454, -0.00661136, 0.00016808, -0.00022501),
       "reciprocating": (0.66534403, -0.01383821, 0.00014736, 0.00712808, 0.00004571, -0.00010326)}
WATER = {"centrifugal": (0.51777196, -0.00400363, 0.00002028, 0.00698793, 0.00008290, -0.00015467),
         "screw": (0.66625403, 0.00068584, 0.00028498, -0.00341677, 0.00025484, -0.00048195),
         "scroll": (1.00121431, -0.01026981, 0.00016703, -0.00128136, 0.00014613, -0.00021959),
         "reciprocating": (0.46140041, -0.00882156, 0.00008223, 0.00926607, 0.00005722, -0.00011594)}

RATED_AIR = 3.517 / (12 / 10.1)      # 90.1 Path A air-cooled full load, EER 10.1: COP 2.96 at 44 F leaving water, 95 F air (AHRI 550/590)
RATED_WATER = 3.517 / 0.560          # 90.1 Path A water-cooled centrifugal >= 300 tons, 0.560 kW/ton: COP 6.28 at 44 F leaving water, 85 F entering condenser
AHRI_RANGE = 10.0 / 1.8              # K: AHRI 550/590's condenser water, 85 F in, 95 F out (3.0 gpm/ton)


def eir(coef, t, x):
    a, b, c, d, e, f = coef
    return a + b * t + c * t * t + d * x + e * x * x + f * t * x


def model(loss, eta, evap_c, cond_c):
    return 1.0 / (loss + np.maximum(cond_c - evap_c, 1.0) / (eta * (evap_c + 273.15)))


def fit(coef, rated, rating, grid, lift_of):
    """Fit loss and eta to COP = rated x EIR(rating) / EIR(t, x), relative error, over grid (leaving water F, x F)."""
    t, x = grid
    target = rated * eir(coef, *rating) / eir(coef, t, x)
    evap, cond = C(t) - 2.0, lift_of(C(x))

    def resid(v):
        return model(v[0], v[1], evap, cond) / target - 1.0

    sol = least_squares(resid, x0=(0.05, 0.7), bounds=([0.0, 0.1], [0.5, 3.0]))
    r = resid(sol.x)
    return sol.x, float(np.sqrt(np.mean(r ** 2))), float(np.max(np.abs(r)))


def eta_for(rated_cop, loss, evap_c, cond_c):
    """The eta that gives rated_cop at a rating point, for a given loss."""
    return (cond_c - evap_c) / ((evap_c + 273.15) * (1.0 / rated_cop - loss))


def main():
    print("Air-cooled (design 0015): leaving water 40-54 F, air 59-115 F (15-46 C), coil air + 12 C")
    t, x = np.meshgrid(np.linspace(40, 54, 15), np.linspace(F(15.0), 115, 57))
    for kind, coef in AIR.items():
        (loss, eta), rms, top = fit(coef, RATED_AIR, (44.0, 95.0), (t.ravel(), x.ravel()), lambda air: air + 12.0)
        print(f"  {kind:14s} loss {loss:.4f}  eta {eta:.3f}  RMS {rms:.1%}  largest {top:.1%}")
    loss_air = 0.0767
    evap, cond = C(44.0) - 2.0, C(95.0) + 12.0
    print(f"  carnot_air at the model's loss {loss_air}: COP 2.96 -> {eta_for(2.96, loss_air, evap, cond):.3f}, 3.61 -> {eta_for(3.61, loss_air, evap, cond):.3f}")

    print("\nWater-cooled (design 0021): leaving water 40-54 F, entering condenser 60-85 F, AHRI range (10 F)")
    t, x = np.meshgrid(np.linspace(40, 54, 15), np.linspace(60, 85, 26))
    out = {}
    for kind, coef in WATER.items():
        (loss, eta), rms, top = fit(coef, RATED_WATER, (44.0, 85.0), (t.ravel(), x.ravel()), lambda cw: cw + AHRI_RANGE + 2.0)
        out[kind] = loss
        print(f"  {kind:14s} loss {loss:.4f}  eta {eta:.3f}  RMS {rms:.1%}  largest {top:.1%}")
    loss_w = round(out["centrifugal"], 4)
    evap, cond = C(44.0) - 2.0, C(85.0) + AHRI_RANGE + 2.0
    print(f"\n  rating point: T_evap {evap:.2f} C, condensing {cond:.2f} C, lift {cond - evap:.2f} K")
    # the rating band through model 1.16: carnot_water 0.62-0.78 with no loss, about code minimum +/- 11% (Lei and Masanet)
    lo, mid, hi = (e * (evap + 273.15) / (cond - evap) for e in (0.62, 0.70, 0.78))
    print(f"  model 1.16's band at the rating point: COP {lo:.2f} / {mid:.2f} / {hi:.2f}")
    etas = [eta_for(c, loss_w, evap, cond) for c in (lo, mid, hi)]
    print(f"  carnot_water at loss {loss_w} for the same band: {etas[0]:.3f} / {etas[1]:.3f} / {etas[2]:.3f}")

    # the smallest lift 90.1's curve covers: 54 F leaving water, 60 F entering condenser, AHRI range
    e_min, c_min = C(54.0) - 2.0, C(60.0) + AHRI_RANGE + 2.0
    print(f"\n  smallest lift on 90.1's curve: {c_min - e_min:.2f} K (54 F water, 60 F condenser)")
    print(f"  90.1 there: COP {RATED_WATER * eir(WATER['centrifugal'], 44, 85) / eir(WATER['centrifugal'], 54, 60):.2f} (code minimum)")
    for name, e in zip(("low", "mid", "high"), etas):
        print(f"  model there, {name} eta: COP {model(loss_w, e, e_min, c_min):.2f}")

    print("\n  model against 90.1 (centrifugal, code minimum), selected points:")
    eta_c = eta_for(RATED_WATER, loss_w, evap, cond)
    for tw, cw in ((44, 85), (44, 75), (44, 65), (44, 60), (54, 85), (54, 60), (40, 85)):
        ref = RATED_WATER * eir(WATER["centrifugal"], 44, 85) / eir(WATER["centrifugal"], tw, cw)
        m = model(loss_w, eta_c, C(tw) - 2.0, C(cw) + AHRI_RANGE + 2.0)
        old = min(0.72 * (C(tw) - 2.0 + 273.15) / (C(cw) + AHRI_RANGE + 2.0 - C(tw) + 2.0), 8.0)
        print(f"   {tw} F / {cw} F: 90.1 {ref:.2f}, model {m:.2f}, model 1.16 (0.72 of Carnot, cap 8) {old:.2f}")

    # second law: with the loss, COP stays below Carnot for every eta in the band, at any lift up to 60 K and T_evap 0-30 C
    lift = np.linspace(1.0, 60.0, 600)
    worst = max(float(np.max(model(loss_w, e, te, te + lift) / ((te + 273.15) / lift))) for e in etas for te in (0.0, 15.0, 30.0))
    print(f"\n  largest COP / Carnot COP over the band: {worst:.3f}")


if __name__ == "__main__":
    main()
