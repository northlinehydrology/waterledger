# 0016: The operator's switch setting (model 1.16)

Status: **decided Nov 15, 2026 (Andrew: sample a range, not very wide, with defensible ends). Built on branch
`chiller-temperature-curve` with design 0015; not released.** Found by Northline's cooling checks against operators' stated
settings and time on water (Nov 15, 2026).

## What was wrong

Assist (dry coolers with pads) and hybrid go wet at a switch point. Through model 1.15 that point was the loop's limit, the
dry-bulb where a dry coil can no longer hold the loop's supply, plus a margin of -2 to 2 K, kept within 21.1-35.1 C (the
70-95 F a controller patent allows, US 12,426,214 B1). On the shared and chilled plants the limit is low, about 13 C and
below 0 C, so every draw sat at the 21.1 C floor: the model put water ahead of chillers from 70 F up.

Operators who state a setting use 85-86 F: Microsoft's direct-air fleet and Wisconsin campus, 85 F (29.4 C); Meta El Paso,
about 86 F (30 C), from its utility. Between the loop's limit and that setting they run chillers, trading electricity for
water. At 21.1 C the model's hours on water were 3 to 20 times what operators say (Wisconsin 16% of hours against under 5%,
Sidney 22% against 3%, Virginia 28% against 10%).

## Decision

1. **A sampled operator's setting, `switch_setting`, 26.5-32.0 C** (an operating setting, heat_rejection.OPERATING; the
   data center's and the battery plant's own ranges). The ends are the settings operators' own stated time on water implies
   at their sites, from ERA5 hourly dry-bulb, 2015-2024 ([../methods/switch-setting/implied.md](../methods/switch-setting/implied.md)):

   | Site | Stated | Implied setting |
   |---|---|---|
   | Microsoft, Northern Virginia | about 10% of the year | 26.5 C |
   | AWS, Falls Township, PA | outside air about 94% of the year | 28.0 C |
   | AWS, Sidney, OH | about 3% of the year | 28.2 C |
   | Microsoft, metro Atlanta | the hottest ~55 days | 30.5 C |
   | AWS, New Carlisle, IN | about 7 days a year | 32.0 C |
   | Microsoft, Phoenix; Wisconsin | up to 40%; under 5% | at least 27.4; at least 25.2 C |

   The two stated settings, 29.4 and 30 C, sit at its middle (29.25 C). Uniform, as every other range.
2. **The switch is the later of the setting and the loop's limit plus the margin**, still within 21.1-35.1 C:

       switch = clip(max(switch_setting, loop_limit + switch_margin), 21.1, 35.1)

   Below the loop's limit the dry coil holds the loop and nothing needs water or chillers. Between the limit and the
   setting, chillers carry what the dry coil can't (electricity). Above both, water. Where the limit is above the setting,
   as in a warm liquid loop, water waits for the limit, as before.
3. **The battery plant takes the same range [A]**: no battery plant states a setting, and its hybrid has the same choice
   between chillers and water. The gas plant's `switch_on` (20-30 C) is a condenser setting with no chillers behind it and
   is unchanged.
4. **`switch_on` still fixes the point** for a site that states its own, as a scenario.

## Why a range and not 85 F

Two operators state a number; the others state time on water, and what those imply spreads 26.5-32 C, partly real
(operators differ) and partly the reading (a share of the year read as hours; ERA5's grid against the site's own air).
Assist's pads and hybrids' wet mode are taken to be run as the operators' outside-air fleets are [A]: the stated settings
are for outside air with pads, the plant most like assist.

## Effects

Stored West Michigan weather (2023-2024), 100 MW of IT, 40 draws, medians, with design 0015 in both:

| Plant, design | Average day, MGD | 1-in-10 peak day, MGD | Peak day, MW |
|---|---|---|---|
| Shared, pads | 0.070 to 0.0066 | 0.57 to 0.23 | 92.74 to 93.41 |
| Shared, hybrid | 0.059 to 0.0085 | 0.58 to 0.33 | 92.25 to 93.26 |
| Warm, pads | 0.053 to 0.0060 | 0.45 to 0.21 | 85.43 to 85.66 |
| Warm, hybrid | 0.039 to 0.0080 | 0.42 to 0.31 | 84.58 to 85.52 |
| Chilled, pads | 0.077 to 0.0072 | 0.62 to 0.25 | 99.82 to 100.24 |
| Chilled, hybrid | 0.062 to 0.0090 | 0.62 to 0.36 | 97.99 to 99.76 |

Average water falls about tenfold for pads and five- to sevenfold for hybrid; the peak day falls by about half, since the
hottest days are above any setting. Electricity rises a little: chillers carry more hours. What pads buy back over dry on the
peak day falls from 0.9 to about 0.25 MW (shared loop); in the hottest hour it stays about 2.7 MW. Dry and towers are
unchanged. The pads' peak day over average day is now about 35, against about 30-31 stated for Mount Pleasant (Wisconsin DNR,
Racine Water Utility); it was 8.

## Checks

The hours on water at each site above, with the model's own draws, against what each operator states: a test in the
packages once the weather for those points is stored with the tests. Until then, `implied_switch.py` reruns the table.
