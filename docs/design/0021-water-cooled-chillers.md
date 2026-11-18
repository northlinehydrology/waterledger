# 0021: Water-cooled chillers on ASHRAE 90.1's curve (model 1.17)

Status: **decided Nov 17, 2026 (Andrew: accepted as built, the name `carnot_water` kept). Merged in model 1.17 (#28); not released.** Proposal P2 of the dry-cooling evidence
note (`docs/research/cooling-power-evidence.md`, branch `cooling-power-evidence`), and the item design 0015 left open.

## What was wrong

Through model 1.16 a water-cooled chiller's COP was a fixed fraction of Carnot with no loss, capped at 8:

    COP = min(carnot_water x T_evap / lift, 8)        lift = entering condenser water + range + 2 - T_evap,  T_evap = supply - 2 C

On the shared and warm loops the chilled water is warm, so the lift is small and the Carnot term runs well above 8. The cap then holds
in nearly every hour a towers plant's chillers run. Two results followed:

- **The hottest hour.** A towers plant's 1-in-10 hottest-hour PUE was 1.264 at every place checked (Grand Rapids, Loudoun County,
  Dallas, Phoenix), whatever the wet-bulb.
- **The dry-towers gap.** Dry's hottest-hour gap over towers was measured against a towers plant whose chillers couldn't respond to
  the weather.

Design 0015 found the same with air-cooled chillers and fixed it with a fitted loss term. It left water-cooled chillers alone because
"the same fit gives a Carnot fraction above 1".

## What 90.1 says

ASHRAE 90.1-2016's default EIR-FT curve for water-cooled centrifugal chillers (COMNET 2017, as given in PNNL-26917, Table 81) is a
biquadratic in leaving chilled water and entering condenser water. It is valid on 40-54 F (4.4-12.2 C) water and 60-85 F (15.6-29.4 C)
condenser water. At full available load, COP = rated COP / EIR-FT.

For a code-minimum machine (0.560 kW/ton, COP 6.28 at AHRI's 44 F / 85 F):

| Leaving water / entering condenser | 90.1 | This form (0021) | Model 1.16 (0.72 of Carnot, cap 8) |
|---|---|---|---|
| 44 F / 85 F | 6.28 | 6.28 | 6.19 |
| 44 F / 75 F | 7.26 | 7.14 | 7.47 |
| 44 F / 65 F | 8.41 | 8.29 | 8.00 |
| 44 F / 60 F | 9.06 | 9.00 | 8.00 |
| 54 F / 85 F | 7.41 | 7.24 | 7.62 |
| 54 F / 60 F | 10.83 | 11.00 | 8.00 |
| 40 F / 85 F | 5.91 | 5.96 | 5.74 |

The curve gains about 1.3% of COP per K of lift where Carnot alone gains about 3%. A Carnot fraction with no loss overstates the
gain at small lifts, and the cap of 8 then took it away entirely. 90.1's own code-minimum machine reaches 10.8 at the smallest lift
its curve covers, so the cap of 8 sat below the standard's minimum there.

## Decision (proposed)

1. **The air-cooled form for water-cooled chillers too**: 1/COP = WATER_CHILLER_LOSS + lift / (carnot_water x T_evap).
   - The loss is 0.0471, fitted by least squares on relative error over the curve's whole range: RMS error 0.8%, largest 2.6%.
   - Screw, scroll and reciprocating curves give 0.065, 0.068 and 0.054. The centrifugal is the large-plant machine.
2. **carnot_water keeps the rating band.**
   - 0.828-1.140 gives COP 5.33-6.70 at AHRI's rating point, as 0.62-0.78 did: code minimum ±11% (Lei and Masanet's COP error).
   - The coefficient now passes 1 at the top. With the loss, the COP stays below Carnot's: the largest ratio is 0.92 at any lift
     from 0.5 to 60 K and any evaporator temperature from 0 to 30 C (test).
   - The name is kept so the draws keep their ranks (each parameter's stream is seeded on its name). The comment says what it is now.
   - Renaming it (for example `chiller_lift_water`) was offered, since "carnot" above 1 could mislead a reader. That would change
     this parameter's draws and so every towers and hybrid number. Andrew kept the name (Nov 17).
3. **No gain below 90.1's smallest lift** (WATER_MIN_LIFT, 12.89 K, which replaces the cap of 8).
   - That lift is 54 F leaving water and 60 F entering condenser water, with AHRI's 10 F range.
   - Below it the chiller's COP holds at its value there: 9.8-11.5 across the band, 10.7 at the middle, against 90.1's code-minimum
     10.8 [A].
   - Reasons:
     - no published full-load curve goes lower;
     - makers' figures below it are part-load values (York's YZ "below 0.100 kW/ton at part load"; IPLV weights), which the model
       doesn't represent separately, as 0015 also found;
     - field measurements run well below catalogue values (GSA GPG-031, 2017: a magnetic-bearing chiller averaged 0.699 kW/ton,
       COP 5.0, in service).
   - A floor on the lift ties the limit to the standard's own range rather than to a number with no source.
   - The air-cooled cap (5-7.6, Andrew's Nov 15 decision) is unchanged.
4. **Air-cooled correction.**
   - Design 0015 set `carnot_air` to 0.571-0.761 to "keep the rating band", COP 2.96-3.61 at the rating point.
   - 0.761 gives 3.61 exactly. 0.571 is the joint fit's own value, and with the fitted loss it gives 2.91 there, 1.7% under.
   - The low end is now 0.584, which gives 2.96, as 0015 meant. Air-cooled COPs at the low end of the range rise about 2%.
   - The fit script reproduces 0015's fit within 1% (loss 0.0773 and 0.569 against 0.0767 and 0.571; its grid differs a little).
     0.0767 is kept.

## What it changes and what it doesn't

- **Changes:**
  - towers and hybrid plants, whenever chillers run;
  - the battery cell plants' towers, hybrid and lake loops (`lake_loop` uses the same chiller);
  - dry and pads, through the `carnot_air` correction only.
- **Doesn't change:** water. Less chiller power is less heat to reject, so towers' and hybrid's evaporation falls slightly with it.
- **Unchanged:**
  - offsets (2 K evaporator, 2 K condenser, 12 K air-cooled coil);
  - tower approach and range;
  - the economizer;
  - every other parameter's draws.

## Effect

Model 1.16 against 1.17's chiller change alone (in memory, the same draws, seed and station correction; 100 MW of IT, shared loop,
p50). The grid fix (P6) and the outside-air design (0022) are not in these numbers.

| Place | Plant | Design | PUE a year, 1.16 → 1.17 | hottest-hour PUE, 1.16 → 1.17 | hottest hour, MW, 1.16 → 1.17 | evaporated, MGD, 1.16 → 1.17 |
|---|---|---|---|---|---|---|
| Grand Rapids | shared | dry | 1.175 → 1.175 | 1.343 → 1.340 | 134.3 → 134.0 | 0.000 → 0.000 |
| Grand Rapids | shared | hybrid | 1.175 → 1.174 | 1.306 → 1.304 | 130.6 → 130.4 | 0.007 → 0.007 |
| Grand Rapids | shared | towers | 1.137 → 1.134 | 1.269 → 1.257 | 126.9 → 125.7 | 0.524 → 0.522 |
| Grand Rapids | chilled | towers | 1.221 → 1.217 | 1.342 → 1.342 | 134.2 → 134.2 | 0.563 → 0.561 |
| Grand Rapids | warm | towers | 1.114 → 1.113 | 1.179 → 1.173 | 117.9 → 117.3 | 0.514 → 0.514 |
| Loudoun County | shared | dry | 1.192 → 1.192 | 1.356 → 1.352 | 135.6 → 135.2 | 0.000 → 0.000 |
| Loudoun County | shared | hybrid | 1.191 → 1.190 | 1.306 → 1.304 | 130.6 → 130.4 | 0.013 → 0.013 |
| Loudoun County | shared | towers | 1.150 → 1.142 | 1.268 → 1.255 | 126.8 → 125.5 | 0.541 → 0.539 |
| Loudoun County | chilled | towers | 1.237 → 1.233 | 1.338 → 1.339 | 133.8 → 133.9 | 0.584 → 0.584 |
| Loudoun County | warm | towers | 1.120 → 1.117 | 1.177 → 1.169 | 117.7 → 116.9 | 0.527 → 0.526 |
| Dallas | shared | dry | 1.233 → 1.233 | 1.378 → 1.377 | 137.8 → 137.7 | 0.000 → 0.000 |
| Dallas | shared | hybrid | 1.228 → 1.226 | 1.309 → 1.306 | 130.9 → 130.6 | 0.044 → 0.044 |
| Dallas | shared | towers | 1.176 → 1.163 | 1.269 → 1.258 | 126.9 → 125.8 | 0.583 → 0.577 |
| Dallas | chilled | towers | 1.268 → 1.265 | 1.343 → 1.343 | 134.3 → 134.3 | 0.631 → 0.630 |
| Dallas | warm | towers | 1.129 → 1.125 | 1.180 → 1.173 | 118.0 → 117.3 | 0.561 → 0.559 |
| Phoenix | shared | dry | 1.258 → 1.257 | 1.404 → 1.403 | 140.4 → 140.3 | 0.000 → 0.000 |
| Phoenix | shared | hybrid | 1.246 → 1.241 | 1.314 → 1.308 | 131.4 → 130.8 | 0.099 → 0.098 |
| Phoenix | shared | towers | 1.152 → 1.144 | 1.268 → 1.255 | 126.8 → 125.5 | 0.594 → 0.592 |
| Phoenix | chilled | towers | 1.269 → 1.260 | 1.339 → 1.340 | 133.9 → 134.0 | 0.655 → 0.651 |
| Phoenix | warm | towers | 1.120 → 1.118 | 1.177 → 1.170 | 117.7 → 117.0 | 0.580 → 0.579 |

The shared plant's three designs at every place, and towers on the other two plants. Every plant and design is in
`docs/methods/chillers/effect.md`.

**What it shows.**
- **Towers.**
  - Yearly PUE falls 0.003-0.013, most in Dallas, where towers' chillers run longest.
  - The hottest hour falls about 1.2 MW per 100 MW on the shared and warm plants. On the chilled plant (7-13 C water) the lift
    stays above 90.1's range, and nothing moves.
  - Evaporation falls up to 1%, because less chiller power means less heat to reject.
- **Dry and pads.** They move only through the `carnot_air` correction, by 0.001-0.004 at most.
- **Dry's gap over towers (shared plant).**
  - Yearly, it grows to 3.6% in Grand Rapids, 4.4% in Loudoun County, 6.0% in Dallas and 9.9% in Phoenix (was 3.3, 3.7, 4.9 and
    9.2%).
  - In the hottest hour it grows by about 1.2 MW per 100 MW.
- **Towers' hottest hour is still nearly the same everywhere** (PUE 1.255-1.258 at p50). That is now physics, not the cap:
  - the four places' 1-in-10-year hottest-hour wet-bulbs are within about 2 K;
  - 90.1's curve gives about 1.3% of COP per K of lift;
  - so the chillers' power differs by a few kW per MW of IT.
  - The evidence note's "pinned at 1.264 by the cap" was half right: the cap made it exactly the same, and the physics makes it
    nearly the same.

## Fit and tests

- `docs/methods/chillers/fit_chillers.py` holds 90.1's coefficients (Tables 80 and 81), the fit for both chiller types, and the table
  above. 0015's fit was not committed; this script covers it too.
- `tests/test_chillers.py` reads the script and checks:
  - the fitted loss;
  - the water-cooled form within 3% of 90.1 everywhere on its range;
  - the air-cooled form's error;
  - both rating bands;
  - COP below Carnot;
  - COP falling with lift;
  - the floor.

## Open

- **Part load.** Makers' part-load COPs run above the full-load curve; the model still has no part-load term (as in 0015).
- **The condenser offsets** (2 K) stay an assumption [A]. The fit's slope doesn't depend on them; the loss does slightly.
