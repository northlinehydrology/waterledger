# 0015: Air-cooled chillers that respond to the air (model 1.16)

Status: **decided Nov 15, 2026 (Andrew: the fitted loss term; the cap sampled over 5-7.6 after a search of makers' data found
no single value). Built on branch `chiller-temperature-curve`; not released.** Found in the Clam River study's closed-loop
set (clam-basin-study `AUDIT.md`, Nov 15).

## What was wrong

Through model 1.15 a chiller's COP was a fixed fraction of Carnot, capped:

    COP = min(carnot x T_evap / (T_cond - T_evap), cap)        T_evap = supply - 2 C, in K
    air-cooled: T_cond = air at the coil + 12 C, carnot_air 0.45-0.55, cap 5

On the shared and warm loops the chilled water is warm (about 16-28 C on the shared loop), so the lift is small and the
Carnot term runs well above 5. The cap then holds at every air temperature a Great Lakes summer has. An air-cooled chiller
drew the same power at 25 C as at 33 C, so a dry plant's hot hours cost no more than its mild ones, and adiabatic pads,
which cool the air ahead of the coil, bought back nothing. On the stored West Michigan weather (100 MW of IT, shared loop,
40 draws) dry and pads differed by 0.1 MW on the 1-in-10-year peak day and not at all in the hottest hour. The Clam study's
peak-day table showed the same (85.9 MW for both).

Real air-cooled chillers lose efficiency as the air warms. ASHRAE 90.1's reference curves (below) give 2.0-2.7% of COP per K
of air at the rating point; the Carnot term gives 2.4%, so the form was right and the cap was what removed the response.

## Decision

1. **A fixed-loss term**: 1/COP = loss + lift / (carnot_air x T_evap),
   capped. The loss stands for what does not shrink with the lift: compressor and motor losses, the condenser fans.
   For air-cooled chillers the loss is 0.0767, fitted by least squares on relative error to ASHRAE 90.1's default EIR-FT
   curve for air-cooled screw chillers (COMNET 2017, as given in PNNL-26917, Table 80) over its leaving-water range,
   4.4-12.2 C, and the hours chillers run, air 15-46 C: RMS error 4.6%, largest 14%. Scroll and reciprocating curves fit
   with 0.068 and 0.089.
2. **carnot_air is refitted to keep the rating band**: 0.571-0.761 gives COP 2.96-3.61 at the rating point (6.7 C leaving
   water, 35 C air), as 0.45-0.55 did. 2.96 is EER 10.1, 90.1's Path A full-load minimum.
3. **The cap is sampled, 5-7.6** (`air_cop_cap`, in the well-built-plant group). No published value sets it:
   - 90.1's curve flattens in cool air; fitted over its whole range (4.4-46 C) the loss is 0.132, a ceiling of 7.6, for
     minimum-efficiency machines on cold water;
   - makers' part-load figures run higher. Mitsubishi's MECH-iC 500 ton on about 19 C water: 0.559 kW/ton at 75% load and
     30 C air (COP 6.3), 0.407 at 50% and 20 C (COP 8.6), stated as illustrative. Daikin's Pathfinder: IPLV over 22 EER
     (COP 6.4) on 6.7 C water. Trane's TCA sheet gives no efficiency;
   - 5 was the value through model 1.15 [A].
   Andrew chose 5-7.6 as the range; the makers' figures above 7.6 are part-load values, which this model does not
   represent separately.
4. **Water-cooled chillers are unchanged** (no loss, cap 8). 90.1's water-cooled curves are flatter than a Carnot fraction
   with this model's offsets: the same fit gives a Carnot fraction above 1. That is a separate question, left open.

The fit is extrapolated in leaving water above 12.2 C through the lift, which is the physical part of the form; the curves
themselves are biquadratics valid only on 4.4-12.2 C water and are not used directly.

## Check against a published point

Mitsubishi's MECH-iC sheet: COP 3.88-3.95 at full load, 42 C air, water 18.9/27.8 C (AHRI 550/590 certified capacity). The new
form gives 3.33-4.08 there across carnot_air's range. The old one gave 3.5-4.3, below its cap, so the hot end changes little.

## Effect (stored West Michigan weather, 2023-2024, 100 MW of IT, 40 draws, medians)

| Plant | Design | Peak day MW, 1.15 | Peak day MW, 1.16 | Hottest hour MW, 1.15 | 1.16 | Annual PUE, 1.15 | 1.16 |
|---|---|---|---|---|---|---|---|
| Shared | Dry | 94.75 | 93.66 | 133.4 | 134.4 | 1.192 | 1.186 |
| Shared | Pads | 94.65 | 92.74 | 133.4 | 131.7 | 1.189 | 1.179 |
| Shared | Hybrid | 93.64 | 92.25 | 132.2 | 129.4 | 1.187 | 1.181 |
| Shared | Towers | 89.42 | 89.42 | 127.8 | 127.8 | 1.144 | 1.144 |
| Warm | Dry | 88.22 | 87.35 | 127.8 | 125.3 | 1.141 | 1.138 |
| Warm | Pads | 86.19 | 85.43 | 123.3 | 121.8 | 1.136 | 1.132 |
| Chilled | Dry | 99.85 | 101.18 | 144.4 | 145.6 | 1.297 | 1.298 |
| Chilled | Pads | 98.22 | 99.82 | 140.3 | 142.6 | 1.294 | 1.292 |

- What pads buy back over a dry plant (shared loop): 0.1 to 0.9 MW on the peak day, 0 to 2.7 MW in the hottest hour.
- On the shared loop a dry plant's hottest hour rises 1 MW (the loss term at high lift) while its peak day falls 1.1 MW, because
  the day's milder hours now run above the old cap. On the warm loop both fall.
- The chilled-water plant's cold water keeps its chillers below 5 on hot days, so its hot hours rise by 1-2 MW.
- Pad and hybrid water fall 1-3% on average: less chiller power is less heat to reject. Towers are unchanged.

## What it touches

`heat_rejection.chiller_cop`, `AIR_CHILLER_LOSS`, `EQUIPMENT["carnot_air"]` and `["air_cop_cap"]`; the compiled kernel
(`datacenter/kernel.py`); `physics.SOURCES` and `LINKED`; Michigan's `PARAM_SOURCES`. Battery cell plants share the equipment,
so their dry and assist numbers move too (one model version for every type). Snapshots carry data center numbers, so model
1.16 rebuilds them.

## Open

- Water-cooled chillers: the same treatment needs a form that fits 90.1's flatter curves (item 4).
- Part load: makers' part-load COPs run above the full-load curve; the model has no part-load term.
- The 12 K condenser offset stays an assumption [A].
