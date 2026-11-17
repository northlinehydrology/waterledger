# Dry cooling's electricity: the evidence and model 1.16

Research note, Nov 16, 2026. The question is how much more electricity a data center uses when it rejects heat without
evaporating water, against towers that do. Public material often calls the difference huge. This note checks model
1.16 (waterledger-models 3.24.0, branch `chiller-temperature-curve`, not yet released) against published and disclosed
evidence, design by design and place by place. No code was changed. The changes in section 8 are proposals for Andrew.

## Update, Nov 17, 2026: what came of the proposals (model 1.17)

Andrew asked on Nov 16 for all six proposals in section 8 to be done. P2, P3 and P6 change the numbers and go into model 1.17
(waterledger 3.25.0, branch `model-1.17`, not released, after model 1.16's release); P1's package side is in the same branch;
P1's page and P4-P5's copy are on the Northline repository's branch `claude/zealous-mclean-10341d`. The sections below are
the Nov 16 check of model 1.16 and stand as written; the tables at model 1.17 are `cooling-power-evidence/runs/tables_117.md`
(`tables_117.py`, in memory on `model-1.17`, nothing written to the cache), with a second Arizona Public Service cell
(33.00, -111.25).

| Proposal | Done | Where |
|---|---|---|
| P1, three numbers on the site | The package side: `Site.by_design` returns each design's yearly MWh, hottest-hour MW, the balancing authority's hourly grid water and the differences against towers (design 0020, proposal 1). The cooling-systems page shows the three numbers by design and plant. The calculators' tables go into the trade-off session's build. | waterledger `model-1.17`; Northline `claude/zealous-mclean-10341d` |
| P2, water-cooled chillers on 90.1's curve | Built: a fitted loss (0.0471, within 3% of 90.1's centrifugal curve) and no gain below the curve's smallest lift, in place of the cap of 8 (design 0021) | waterledger `model-1.17` |
| P3, an outside-air evaporative design | Built: `outside_air`, with a sampled pad control (design 0022). Not on the site's buttons until Andrew's local check | waterledger `model-1.17` |
| P4, the base overhead | Kept, and said on the methods pages (option a) | Northline `claude/zealous-mclean-10341d` |
| P5, grid water with and without reservoirs | Said on the methods pages, with each state's balancing authorities both ways | Northline `claude/zealous-mclean-10341d` |
| P6, Arizona Public Service's marginal factor | A real fault, fixed for every balancing authority: EIA-930 spikes screened, a Theil-Sen slope, Palo Verde's own factor, concentrating solar's water as solar (design 0008) | waterledger `model-1.17` |

**What moved, at model 1.17** (shared plant unless named, p50, per 100 MW of IT; `runs/tables_117.md`):

- **Dry's yearly gap over towers.** It is a little wider, because towers' chillers now gain efficiency in mild hours.
  - Shared plant: Grand Rapids 3.6% (was 3.3), Loudoun County 4.3% (3.7), Dallas 6.0% (4.9), Phoenix 9.9% (9.2), the second
    Phoenix cell 9.3%.
  - Chilled plant: 4.8-9.3%. Warm plant: 1.9-6.7%.
- **The hottest hour at 1 GW.** Dry needs 83, 97, 119 and 148 MW more than towers on the shared plant (was 75, 87, 109 and 136),
  and 114-180 MW more on the chilled plant.
- **Towers' hottest hour is still about 1.256 everywhere.** That is now physics, not the cap: the four places' hottest-hour
  wet-bulbs are within about 2 K, and 90.1's curve is flat (design 0021).
- **Grid water.** The power plant water for dry's extra electricity is 3.0-4.4% of the towers' own water in Michigan, Virginia and
  Texas, and 13.3-14.2% at Phoenix's AZPS and SRP.
  - Arizona Public Service's marginal factor on the peak day falls from 7.4 to 0.91 MGD per 100 MW. Its average withdrawal falls
    from 7.2 to 1.0, since Palo Verde now carries its own factor.
- **Outside air (all air-cooled halls).**
  - PUE 1.107 a year at every place, against towers' 1.134-1.163.
  - Water on 1% (Grand Rapids) to 32% (Phoenix) of the hours.
  - Phoenix withdraws 0.25 L per IT kWh, against towers' 1.82 (design 0022's check).
  - With the plant's sampled liquid racks it is 1.122-1.150, and in Phoenix it sits above towers (1.150 against 1.144).

Section 9's paragraphs are updated to these numbers.

Conventions:

- Model numbers are per 100 MW of IT capacity and are medians (p50) over the 400 draws, unless marked central (every
  parameter at its midpoint).
- Evidence labels:
  - **[V]** read in the primary document.
  - **[F]** read by eye off a published figure, about ±0.02 PUE.
  - **[D]** my arithmetic from disclosed numbers.
  - **[S]** search result or secondary source only, unverified.
- Evidence types are named for each source: peer-reviewed, government lab report, standard, company disclosure,
  maker document, trade survey, press, preprint. Peer review is the ideal, not a requirement. Where a source is weaker,
  the note says what kind it is.
- "Dry" is model design `dry`, dry coolers and air-cooled chillers with no evaporation. "Pads" is `assist`, dry coolers
  with adiabatic pads on hot hours. "Hybrid" and "towers" are `hybrid` and `towers`. Plants are `shared` (one facility
  water loop at about 16-28.5 C, the default), `warm` (a separate 30-42 C liquid loop) and `chilled` (7-13 C chilled
  water) (design 0007).

## 1. Short answer

- **Annual energy: the gap is small, and the model's value holds.** Dry over towers is +3.3% (Grand Rapids), +3.7%
  (Loudoun County), +4.9% (Dallas) and +9.2% (Phoenix) on the shared loop. The best like-for-like measured pair is
  Google's air-cooled Storey County campus against its evaporative Henderson campus, both in Nevada: about +0.06 to
  +0.07 PUE, or 5.5-6.5%. LBNL's 2024 simulations give +0.03 to +0.08 for large air-cooled sites, and about zero for
  liquid cooling on warm water. Microsoft calls its increase "nominal". The model sits in the middle of this evidence.
- **Peak capacity: the gap is large, and the model's value holds, perhaps on the low side.** In the hottest hour of a
  1-in-10-year summer, a 1 GW campus needs 75 MW (Grand Rapids) to 136 MW (Phoenix) more with dry than with towers on
  the shared loop. On a chilled-water plant it needs 117-184 MW more.
  - The chiller-level numbers agree with this. At 40-46 C an air-cooled chiller needs about twice the electricity per
    unit of heat that a water-cooled one needs. PNNL-26917's code curve agrees with the model's air-cooled chiller
    within the fit.
  - Amazon's "25% to 35% more electricity" on the hottest days is matched by the model under either reasonable reading.
    Read as cooling overhead, the model gives +28% to +51% over towers in that hour. Read as whole-facility power, the
    model's chilled-water dry plant needs 24-29% more than a plant whose towers need no chillers (the warm loop).
- **Grid water: small next to the towers' own.** The power plant water for dry's extra electricity is 3-6% of what
  towers evaporate on site in Michigan, Virginia and Texas, and about 13% in Phoenix. That uses the model's EIA-923 plant
  factors, which leave out hydropower reservoirs. With factors that include reservoir evaporation, the Arizona result
  can reverse (section 7).
- **Loop temperature is as big a lever as the design.** Dry in Dallas on a 7-13 C chilled-water plant uses 9.6% more
  electricity a year than dry on the shared loop. That is twice the dry-towers gap on the shared loop (4.9%).
- **What the model gets wrong or leaves out (section 8):**
  - Towers' hottest hour is pinned at PUE 1.264 in every climate, because water-cooled chillers sit at the model's COP
    cap of 8 there.
  - The base overhead puts towers at PUE 1.14-1.18, above the 1.08-1.15 that evaporative fleets disclose.
  - There is no direct outside-air evaporative design, the hyperscale archetype the public comparisons are usually
    made against.
  - One grid factor, Arizona Public Service's marginal mix on the peak day, looks wrong.

## 2. Three things that get mixed up

1. **Annual energy**, in MWh a year or as a year-average PUE. This is what a bill, a carbon inventory or an annual
   water-at-the-power-plant figure uses. Dry costs a few percent here because chillers run only in warm hours, and the
   fans and pumps cost about the same in either design.
2. **Peak capacity**, in MW in the hottest hour. This is what a utility plans generation and transmission for. Dry costs
   much more here, because in that hour every chiller runs and an air-cooled chiller works against dry-bulb air, which
   is 10-24 K hotter than the wet-bulb a tower works against.
3. **Grid water**, the water evaporated at the power plants that make the extra electricity. It follows annual energy,
   so it is small. It depends on the grid's mix, and on whether hydropower reservoirs are counted.

Public claims often take a number from the second (a peak-day percentage) or from a no-economizer chilled-water plant,
and use it as if it were the first. Section 6 tests them.

## 3. The model, place by place

Sources of the numbers:

- **Stored model 1.16 ERA5 cell runs**, 1995-2024, corrected to nearby stations:
  - Grand Rapids: `~/.cache/waterledger/era5/runs/model1.16/43.00_-85.75.json`
  - Loudoun County: `39.00_-77.50.json`
  - Dallas: `32.75_-96.75.json`
- **Phoenix (cell 33.50_-112.00).** Arizona's 1.16 cells had not been run yet on Nov 16, so this cell was run in memory
  with the same code, draws, seed and grid factors, corrected to the same three ISD stations. The design dry-bulb went
  from 43.90 to 43.46 C, as in its model 1.11 record. Nothing was written to the cache.

Scripts and outputs are in [cooling-power-evidence/](cooling-power-evidence/) (section 12).

### 3a. PUE and power

Year-average PUE, and power in the 1-in-10-year hottest hour with every computer at capacity (`pue_avg`,
`power_mw_peak_1in10`):

| Place | Plant | Dry | Pads | Hybrid | Towers | Dry over towers, year | Hottest hour MW: dry / pads / hybrid / towers | Dry over towers, hottest hour |
|---|---|---|---|---|---|---|---|---|
| Grand Rapids, MI | shared | 1.175 | 1.175 | 1.175 | 1.137 | +3.3% | 134.3 / 131.0 / 130.6 / 126.9 | +7.5 MW (+5.9%) |
| Grand Rapids, MI | warm | 1.134 | 1.132 | 1.132 | 1.114 | +1.7% | 129.1 / 123.3 / 122.6 / 117.9 | +11.2 MW (+9.5%) |
| Grand Rapids, MI | chilled | 1.277 | 1.276 | 1.275 | 1.221 | +4.6% | 145.8 / 142.1 / 141.5 / 134.2 | +11.7 MW (+8.7%) |
| Loudoun County, VA | shared | 1.192 | 1.190 | 1.191 | 1.150 | +3.7% | 135.6 / 130.8 / 130.6 / 126.8 | +8.7 MW (+6.9%) |
| Loudoun County, VA | warm | 1.143 | 1.141 | 1.141 | 1.120 | +2.1% | 130.1 / 123.0 / 122.6 / 117.7 | +12.4 MW (+10.6%) |
| Loudoun County, VA | chilled | 1.304 | 1.302 | 1.301 | 1.237 | +5.4% | 147.0 / 142.0 / 141.5 / 133.8 | +13.2 MW (+9.8%) |
| Dallas, TX | shared | 1.233 | 1.226 | 1.228 | 1.176 | +4.9% | 137.8 / 131.5 / 130.9 / 126.9 | +10.9 MW (+8.6%) |
| Dallas, TX | warm | 1.170 | 1.160 | 1.163 | 1.129 | +3.6% | 131.7 / 123.9 / 123.2 / 118.0 | +13.8 MW (+11.7%) |
| Dallas, TX | chilled | 1.351 | 1.343 | 1.342 | 1.268 | +6.5% | 149.4 / 142.5 / 141.5 / 134.3 | +15.1 MW (+11.2%) |
| Phoenix, AZ | shared | 1.258 | 1.237 | 1.246 | 1.152 | +9.2% | 140.4 / 131.1 / 131.4 / 126.8 | +13.6 MW (+10.7%) |
| Phoenix, AZ | warm | 1.193 | 1.164 | 1.171 | 1.120 | +6.5% | 133.9 / 123.3 / 123.9 / 117.7 | +16.2 MW (+13.8%) |
| Phoenix, AZ | chilled | 1.379 | 1.356 | 1.358 | 1.269 | +8.6% | 152.4 / 142.2 / 141.6 / 133.9 | +18.4 MW (+13.8%) |

### 3b. A 1 GW campus

The same runs scaled by 10. "Average MW" is at the run's utilization, central 0.65. The peak day is the 1-in-10-year
peak day's average power at the peak load. The last column gives the same difference at the draws' p10 and p90.

| Place | Plant | Average MW, dry / towers | Extra GWh a year, dry | Hottest hour MW, dry / towers | Extra MW, hottest hour | Peak day MW, dry / towers | Extra MW, hottest hour, p10 / p90 |
|---|---|---|---|---|---|---|---|
| Grand Rapids | shared | 765 / 744 | 183 | 1,343 / 1,269 | +75 | 937 / 900 | +61 / +90 |
| Grand Rapids | chilled | 828 / 798 | 261 | 1,458 / 1,342 | +117 | 1,018 / 949 | +113 / +124 |
| Loudoun | shared | 774 / 751 | 202 | 1,356 / 1,268 | +87 | 942 / 898 | +73 / +104 |
| Loudoun | chilled | 844 / 808 | 315 | 1,470 / 1,338 | +132 | 1,024 / 948 | +126 / +141 |
| Dallas | shared | 800 / 765 | 308 | 1,378 / 1,269 | +109 | 957 / 903 | +88 / +127 |
| Dallas | chilled | 877 / 828 | 422 | 1,494 / 1,343 | +151 | 1,039 / 950 | +143 / +163 |
| Phoenix | shared | 816 / 752 | 558 | 1,404 / 1,268 | +136 | 976 / 896 | +115 / +157 |
| Phoenix | chilled | 894 / 826 | 601 | 1,524 / 1,339 | +184 | 1,059 / 946 | +172 / +203 |

The warm plant gives +132 to +162 MW in the hottest hour (Grand Rapids +112) and 132-400 GWh a year (full table in
`cooling-power-evidence/runs/tables.md`).

As shares, the extra energy is 2-9% of the year's electricity. The extra hottest-hour power is 6-14% of the campus's
peak.

### 3c. Where the electricity goes

Central parameters, kW per kW of IT. The base, meaning IT, power losses, lighting and air handler fans, is 1.092 in
every row and is left out. The hottest hour is the year's highest-PUE hour, median over the 30 years. "Chillers on" is
the share of hours with any chiller running.

| Place | Plant | Design | Year: chillers / pumps / fans / PUE | Hottest hour: chillers / pumps / fans / PUE | Hottest hour, dry-bulb / wet-bulb C | Chillers on |
|---|---|---|---|---|---|---|
| Grand Rapids | shared | dry | 0.056 / 0.019 / 0.005 / 1.172 | 0.229 / 0.007 / 0.000 / 1.328 | 34.6 / 23.3 | 42% |
| Grand Rapids | shared | towers | 0.015 / 0.023 / 0.004 / 1.134 | 0.139 / 0.025 / 0.007 / 1.264 | 32.7 / 26.9 | 23% |
| Loudoun | shared | dry | 0.074 / 0.017 / 0.005 / 1.188 | 0.241 / 0.007 / 0.000 / 1.340 | 36.3 / 25.6 | 52% |
| Loudoun | shared | towers | 0.025 / 0.023 / 0.005 / 1.145 | 0.139 / 0.025 / 0.007 / 1.264 | 30.4 / 26.1 | 33% |
| Dallas | shared | dry | 0.119 / 0.013 / 0.004 / 1.228 | 0.264 / 0.007 / 0.000 / 1.363 | 40.6 / 25.5 | 74% |
| Dallas | shared | towers | 0.050 / 0.024 / 0.006 / 1.171 | 0.139 / 0.025 / 0.007 / 1.264 | 32.4 / 26.9 | 52% |
| Dallas | chilled | dry | 0.223 / 0.008 / 0.001 / 1.345 | 0.356 / 0.007 / 0.000 / 1.477 | 40.6 / 25.5 | 98% |
| Dallas | chilled | towers | 0.116 / 0.025 / 0.007 / 1.261 | 0.179 / 0.027 / 0.007 / 1.326 | 35.1 / 27.2 | 90% |
| Phoenix | shared | dry | 0.145 / 0.012 / 0.004 / 1.253 | 0.293 / 0.007 / 0.000 / 1.392 | 45.7 / 21.3 | 84% |
| Phoenix | shared | towers | 0.026 / 0.023 / 0.006 / 1.147 | 0.139 / 0.025 / 0.007 / 1.263 | 30.5 / 25.8 | 32% |

Every plant and place is in `cooling-power-evidence/runs/breakdown_*.json`. What the table shows:

- **The whole gap is chillers.** Pumps and fans cost about the same in both designs; dry's are slightly lower.
- **Code minimums agree.** ASHRAE 90.1 Table 6.8.1-7 puts fan power at about 0.013 kW per kW of heat for open towers
  and 0.014 for air-cooled condensers [D]. The Kaltra dry cooler catalog gives 0.013-0.026 at a 10 K approach [V].
  Neither design has an advantage in fan energy. The difference is the heat sink: dry-bulb against wet-bulb.
- **The towers' hottest hour is 1.264 at every place.** Its chillers carry the whole load at the water-cooled COP cap
  of 8, whatever the wet-bulb (section 5e).
- **Pads and hybrid peak just below the switch setting.** Their highest-PUE hour falls at 29.2 C, the central switch
  setting. Below it, chillers carry what the dry coil can't, and above it, water takes over. Their hottest hour is
  therefore about 1.300 everywhere.

### 3d. What drives the gap

Loudoun County, shared loop, central parameters, one parameter at a time, dry minus towers:

| Case | Year PUE, dry / towers | Gap, year | Hottest hour, dry / towers | Gap, hottest hour |
|---|---|---|---|---|
| central | 1.188 / 1.145 | +3.8% | 1.339 / 1.264 | +5.9% |
| supply air 24 C / 30 C | 1.205 / 1.162 ; 1.171 / 1.129 | +3.7% ; +3.7% | 1.358 ; 1.320 against 1.264 ; 1.259 | +7.4% ; +4.8% |
| air-cooled chiller at code minimum (carnot_air 0.571) / best (0.761) | 1.191 ; 1.186 | +4.0% ; +3.6% | 1.364 ; 1.319 | +8.0% ; +4.4% |
| air-cooled COP cap 5 / 7.6 | 1.204 ; 1.182 | +5.1% ; +3.3% | 1.339 | +5.9% |
| dry cooler approach 5 K / 10 K | 1.175 ; 1.200 | +2.7% ; +4.8% | 1.339 | +5.9% |
| tower approach 2.8 K / 6.7 K | towers 1.134 ; 1.157 | +4.8% ; +2.7% | 1.264 | +5.9% |
| liquid share 0 / 1 | 1.202 / 1.159 ; 1.173 / 1.131 | +3.8% ; +3.8% | | +5.9% ; +5.9% |
| UPS 0.99 | 1.134 / 1.093 | +3.8% | 1.278 / 1.206 | +5.9% |

What moves which gap:

- **Annual gap: the approaches and the air-cooled chiller's best COP.** These set how many hours each design can
  economize and how hard the chillers work in mild air.
- **Hottest-hour gap: the air-cooled chiller's efficiency and the loop temperature.**
- **Towers' hottest hour: none of these.** It sits at the cap.
- **Base overhead (UPS): every PUE, not the gap.**

## 4. The evidence

The full source logs, with URLs, page numbers and quotes, are in
[cooling-power-evidence/sources-operators.md](cooling-power-evidence/sources-operators.md) and
[cooling-power-evidence/sources-equipment.md](cooling-power-evidence/sources-equipment.md). The citations are in
section 11. Here is what each source says about dry against evaporative.

| Source | Type | Dry over evaporative | Annual or peak |
|---|---|---|---|
| LBNL 2024 (Shehabi et al.), Fig. 4.4, p. 46 [F] | government lab report, simulation over 965 stations | Large sites, air-cooled IT: dry cooler with adiabatic assist about 1.20 against waterside economizer about 1.12 (+0.08); airside with adiabatic, air-cooled chiller about 1.17 against water-cooled about 1.14 (+0.03). Liquid IT at W45: dry cooler about 1.09-1.10 against towers about 1.13 (dry level or lower). Midsize: +0.2 to +0.3 | annual |
| LBNL 2024, p. 45 [V] | same | "While air-cooled chillers use no water, they use more energy." | qualitative |
| Lei and Masanet 2022, Fig. 4 [F] (preprint rs-769999) | peer-reviewed (preprint read) | Midsize, no economizer, air-cooled against water-cooled chiller: zone 5A about +0.06, 4A +0.10, 3A +0.15, 2B (Phoenix-type) +0.33. No large-site dry case | annual |
| Google 2025 Environmental Report and efficiency page [V], arithmetic [D] | company disclosure, measured | Storey County NV (air-cooled) 1.16 (2024), against Henderson NV (evaporative) 1.09: +0.07, with the air-cooled campus in the cooler climate. Trailing 12 months, 2026: 1.15 against 1.09. Mesa AZ (air-cooled, first year) 1.22 (Q1) and 1.28 (Q2, 2026), against Midlothian TX 1.08 and 1.12. Dublin (air-cooled, mild) 1.08 | annual, seasonal |
| Google (Hölzle, Nov 2022) [V] | company disclosure | Water-cooled "about 10% less energy". Base not stated | annual |
| Microsoft (Solomon, Dec 2024; 2025 sustainability report, p. 36) [V] | company disclosure | Mechanical cooling "will increase our power usage effectiveness", a "nominal increase in our annual energy usage". No number. The extra power is offset with economizing chillers on warmer water | annual |
| Amazon (Jun 11, 2026) [V] | company disclosure | Chillers "require 25% to 35% more electricity" than evaporative on the hottest days. Base not stated. Free air about 90% of the time; water above about 85 F | peak |
| Crusoe, Abilene TX [V] | company disclosure | Closed-loop liquid cooling on air-cooled chillers, annualized design PUE 1.2-1.4 | annual, design |
| Karimi et al. 2022, RCR 181:106194 (abstract) | peer-reviewed, measured | Two Phoenix colocation sites: air-cooled chillers about 13% higher PUE, 66% lower source water use | annual |
| Karimi et al. 2025, Appl. Therm. Eng. 276:126802 (abstract) | peer-reviewed, hourly model | Phoenix: air-cooled chillers the most energy; pre-cooling them saves 11% | annual |
| Uptime Institute Briefing Report 200 (Talib and Dietrich, Apr 2026), summary only [V] | trade research on operating data, paywalled | Well-designed dry and adiabatic systems "can match evaporative cooling PUE" in ASHRAE zones 2-6 | annual |
| Uptime Global Survey 2025 [V] | trade survey | Average PUE 1.54; sites of 20 MW or more 1.44 | context |
| NREL ESIF thermosyphon, Sickinger et al. 2018 [V] | government lab, measured 24 months | Dry stage ahead of towers on a 29 C loop: on-site water 1.42 to 0.70 L/kWh, PUE about 1.03-1.06 unchanged | annual |
| Vertiv 2020, Ashburn VA, 3 MW [V] | maker white paper | Free-cooling air-cooled chiller pPUE 1.13 with no water; adiabatic about 0.01 better; indirect evaporative about 0.02 better again. Air-cooled has the larger peak load | annual |
| Schneider WP 220 (2026), via TechTarget | maker white paper, secondary | 100 MW AI site, Dallas: raising the chip loop from 32 to 45 C cuts WUE 66% with PUE change under 1% | annual |
| ASHRAE 90.1-2019 Addendum x, Table 6.8.1-3 [V] | standard | Air-cooled chiller minimum COP 2.96 at 35 C (fans included); water-cooled centrifugal over 600 tons 6.28 (tower and pumps excluded) | rating point |
| PNNL-26917 Tables 77-83 (COMNET curves) [V], evaluated [D] | government lab | Air-cooled screw at 6.7 C water: power per kW of cooling 1.154x rated at 105 F, 1.241x at 110 F, 1.334x at 115 F; capacity 0.885-0.945 | peak |
| SPX / Swanson Rink (2026) [V] | maker (tower vendor) | No economizer: air-cooled 1.25-1.34 kW/ton against water-cooled 0.43-0.46; about 2.9x the cooling energy | annual, no economizer |
| ACHR News / Baltimore Aircoil (2014) [V] | trade press, vendor analysis | 500-ton office plant: peak 628 kW air-cooled against 345 kW water-cooled | peak, comfort cooling |
| Mokkapati and Das (2026), engrXiv | preprint, by an adiabatic-cooler firm | 107 F fluid: dry cooler fans 0.7-1.0% of heat rejected (El Paso); dry can't reach the target in Phoenix or Las Vegas at design | annual and design |
| Alston, Love and Haider (2026), arXiv 2609.25437 [V] | preprint (University of Michigan) | Michigan, 200 MW: air-cooled chiller +32% facility energy. The PUEs are LBNL's upper midsize endpoints, "worst-case configurations" in the authors' words | annual, worst case |

The equipment side, from the agents' arithmetic on the standard's numbers [D]:

- **A code-minimum chilled-water plant in Dallas's hottest hour** (about 105-110 F, about 100 MW of heat):
  - air-cooled chillers: about 39-42 MW;
  - water-cooled chillers plus tower fans and pumps: about 19 MW;
  - gap: about 20-25 MW.
- **The model's chilled-water gap is 15.1 MW at p50 and 16.3 at p90** (section 5b explains the difference).

## 5. Design by design: what holds and what doesn't

### 5a. Dry on the shared loop (the default)

**Annual: holds.**

- **The best measured comparisons.**
  - Google's Nevada pair: +0.06 to +0.07. Its air-cooled site is in the cooler climate, so the like-for-like gap may be
    a little larger.
  - LBNL's large-site air-cooled cases: +0.03 to +0.08.
- **The model:** +0.038 (Grand Rapids), +0.042 (Loudoun) and +0.057 (Dallas).
- **Phoenix.** The model's +0.106 (+9.2%) sits below Karimi et al.'s +13% for two Phoenix colocation sites. Those are
  older chilled-water designs; the model's chilled plant in Phoenix gives +8.6%. Read place by place, the model may run
  slightly low in hot, dry climates, within the spread of one measured pair.
- **The climate order** (Michigan < Virginia < Texas < Arizona) matches Lei and Masanet's.
- **The parity claims** (Uptime 2026, LBNL's W45 case, Schneider) are for warm liquid loops or the best designs. The
  model gives near parity there too (5c).

**Hottest hour: holds.** The air-cooled chiller is fitted to ASHRAE 90.1's reference curve (design 0015). At Dallas's
hottest hour (40.6 C, 6.7 C water) the model gives COP 2.64 at the code-minimum end of `carnot_air`, against 2.57 from
the curve. The model's 6-11% more facility power in that hour is 28-51% more cooling overhead. That is the size of
Amazon's 25-35% and the vendors' 10-40% (Data Center Knowledge, Oct 2026, quoting vendors), if those are read as cooling
electricity.

### 5b. Dry on a chilled-water plant

**Holds, at the efficient end.** Annual +4.6% (Grand Rapids) to +8.6% (Phoenix), in line with Lei and Masanet's large
cases and Google's fleet "about 10%".

The hottest-hour gap of 12-18 MW per 100 MW sits below the 20-25 MW from code-minimum arithmetic. There are two reasons:

- the model samples chilled water at 7-13 C, central 10 C, against the 6.7 C rating;
- it samples air-cooled chillers across the rating band, COP 2.96-3.61 at the rating point, not at the code minimum.

At 6.7 C water and code-minimum chillers the model gives about 20 MW in Dallas [D], which is the code-minimum arithmetic.
So the model's p50 is a mid-efficiency plant, and its p90 (16.3 MW) does not reach the code minimum. That is the
model's choice of range, stated in `heat_rejection.EQUIPMENT`. It is not a physics error.

### 5c. Dry on the warm liquid loop

- **Annual: holds.** The gap is the smallest of the three plants: +1.7% (Grand Rapids) to +6.5% (Phoenix).
  - LBNL's W45 dry cooler comes out level with or below towers.
  - Schneider's 32-45 C loops show under 1% PUE change from evaporation.
  - The model's warm loop is 30-42 C facility water, not 45 C, and its air hall stays on the cooler loop, so a small
    positive gap is right.
- **Hottest hour: holds in physics, and it is the case to explain.** Towers keep a 36 C liquid loop with no chillers on
  the hottest day. A dry cooler can't once the air is above about 26 C, so the dry plant runs air-cooled chillers. The
  result is the largest hottest-hour gap in percent (+9.5% to +13.8%).
  - Real warm-loop designs avoid this with pads above 32 C (Schneider RD109). In the model that is the pads design,
    which takes 6-11 MW per 100 MW off dry's hottest hour on the warm loop.

### 5d. Pads and hybrid

- **Year-average PUE: the same as dry in Grand Rapids and Loudoun.** Since model 1.16 the operator's switch setting
  (26.5-32 C, design 0016) keeps the pads off until the air is warm. Below it, chillers carry what the dry coil can't,
  as Microsoft, Amazon and Meta run their fleets.
- **What pads and hybrids buy is peak capacity.** They take 3.3 MW (Grand Rapids) to 9.3 MW (Phoenix) per 100 MW off dry's hottest hour on
  the shared loop.
- **The annual result agrees with Vertiv.** Vertiv's Ashburn case puts adiabatic assist about 0.01 pPUE better than a
  free-cooling air-cooled chiller plant [V]; the model gives 0.002 in Loudoun.

### 5e. Towers

- **The gap: holds.**
- **Absolute PUE: high.** The model's towers run 1.137-1.176 on the shared loop. Evaporative fleets disclose lower:
  - Google 1.08-1.12 by campus;
  - Meta 1.08 fleet;
  - AWS 1.12-1.15 by region.
  - The cause is the base overhead, 1.092 at central: UPS 0.90-0.99, distribution 0-2% and air handler fans. LBNL 2024
    uses the same 90-99% UPS range for hyperscale (Table 4.3). With UPS at 0.99 the Loudoun towers fall to 1.093. This
    changes every design's PUE and power, but not the gap (section 8, P4).
- **Hottest hour: pinned at 1.264 in every climate.** On the shared loop at peak the water-cooled chiller's Carnot
  term exceeds its cap of 8 [A], so the towers' hottest hour does not respond to the wet-bulb.
  - Real centrifugal chillers on warm (about 21 C) chilled water often run better than COP 8. For example, ASHRAE
    90.1's Path B IPLV allows COP 9.26 at part load.
  - Design 0015 left water-cooled chillers open for the same reason: 90.1's water-cooled curves are flatter than a
    Carnot fraction.
  - If the cap or form changes, the towers' hottest hour falls in mild wet-bulb climates and dry's hottest-hour gap
    grows by a few MW per 100 MW. The current value understates the gap a little. It does not overstate it.
- **Water: in range.** The model's towers consume 1.27-1.43 L per IT kWh (`wue_l_per_kwh`, p50). NREL measured 1.42 for
  towers alone at ESIF. Evaporating all the heat at the model's evaporative ratio gives about 1.2-1.4.

### 5f. A design the model doesn't have

Meta, Amazon and Microsoft's older fleet cool with outside air and direct evaporative pads. There is no water loop and,
in most hours, no chillers:

- Meta's fleet runs PUE 1.08 with about 0.19 L per IT kWh withdrawn;
- AWS 1.12-1.15 with 0.06-0.39;
- LBNL's large-site "airside economizer with adiabatic" case runs about 1.14-1.17.

This is the lowest-power design with low water, and it is what Amazon compares chillers against. The model's pads
design is dry coolers with pads ahead of the coil, which still needs chillers in hot hours on a shared loop, so it does
not represent it. The switch settings in design 0016 come from these fleets. Section 8, P3.

## 6. The popular claims, tested

| Claim | Where | Holds? |
|---|---|---|
| "Chillers take a huge amount of electricity" | common in public comment | **For the chiller itself, at the peak, yes.** An air-cooled chiller at 40-46 C runs COP about 2.5-3.8, against 6-8 for water-cooled. **For the facility over a year, no.** Chillers run 23-84% of hours, mostly at part lift, and the facility difference is 2-9% |
| Evaporative "25% to 35%" less electricity on peak days | Amazon 2025-2026 | **Yes, as cooling overhead or against a chiller-free plant.** The model gives +28% to +51% cooling overhead in the hottest hour (shared loop), and +24% to +29% whole-facility for a chilled-water dry plant against a chiller-free warm-loop tower plant |
| Water-cooled "about 10% less energy" | Google 2022 | **Yes for chilled-water and hot-climate air-cooled sites** (model chilled: +4.6% to +8.6%; Phoenix shared +9.2%; Nevada pair about 6%). It overstates warm-loop designs |
| Air-cooled uses about 3x the energy | tower vendors (SPX / Swanson Rink) | **Only for cooling energy with no economizer.** It is about 0.35 against 0.12 pPUE [D]. No large current design runs that way |
| Air-cooled chiller +32% energy, Michigan | Alston et al. 2026 preprint | **Worst-case midsize PUEs (2.32 against 1.76)**, by the authors' own description. Not a large modern campus |
| "Nominal" increase | Microsoft 2024 | **Yes over a year.** Not at the peak, which Microsoft doesn't address |

The honest one-line version: dry cooling costs a few percent more electricity over a year and 6-14% more in the
hottest hour. On the hottest hours the cooling plant itself draws a third to a half more.

## 7. Grid water: what dry's extra electricity costs at the power plants

The cell runs carry `grid_<BA>_<kind>`: the campus's hourly electricity times the hour's water intensity at the
balancing authority's plants (design 0008). The intensity comes from EIA-930 hourly generation by fuel and EIA-923
cooling water, average and marginal mix. It is MGD per 100 MW of IT, average day, with the peak day in brackets:

| Place | Balancing authority | Plant | Towers, consumed on site | Grid consumed, dry / towers | Dry's extra, average mix | Dry's extra, marginal mix | Dry's extra as a share of towers' own |
|---|---|---|---|---|---|---|---|
| Grand Rapids | MISO | shared | 0.524 (0.757) | 0.574 / 0.558 | +0.017 (+0.027) | +0.014 | 3.2% (3.5%) |
| Grand Rapids | MISO | chilled | 0.563 (0.800) | 0.623 / 0.600 | +0.023 (+0.045) | +0.021 | 4.0% (5.6%) |
| Loudoun | PJM | shared | 0.541 (0.763) | 0.525 / 0.509 | +0.016 (+0.028) | +0.010 | 2.9% (3.7%) |
| Loudoun | PJM | chilled | 0.584 (0.809) | 0.574 / 0.549 | +0.025 (+0.051) | +0.016 | 4.2% (6.4%) |
| Dallas | ERCOT | shared | 0.583 (0.793) | 0.456 / 0.436 | +0.020 (+0.026) | +0.019 | 3.4% (3.2%) |
| Dallas | ERCOT | chilled | 0.631 (0.838) | 0.499 / 0.472 | +0.028 (+0.036) | +0.028 | 4.4% (4.3%) |
| Phoenix | AZPS | shared | 0.594 (0.820) | 0.965 / 0.889 | +0.075 (+0.092) | +0.087 | 12.7% (11.2%) |
| Phoenix | SRP | shared | 0.594 (0.820) | 0.997 / 0.918 | +0.079 (+0.066) | +0.045 | 13.2% (8.0%) |
| Phoenix | WALC | shared | 0.594 (0.820) | 0.267 / 0.247 | +0.021 (+0.038) | +0.008 | 3.5% (4.6%) |

PJM and other combinations are in `cooling-power-evidence/runs/tables.md`.

What it shows:

1. **Dry saves almost all of the water, even counting the power plants.**
   - Its extra electricity costs 3-6% of the towers' own water in Michigan, Virginia and Texas, and 13% on Phoenix's two
     main utilities.
   - Per unit of electricity, a power plant would have to consume more water than these to make the two designs equal
     [D]:

     | Place | Break-even, gal per kWh |
     |---|---|
     | Grand Rapids | 10 |
     | Loudoun | 9.8 |
     | Dallas | 6.9 |
     | Phoenix | 3.9 |

   - No thermoelectric fleet comes close. Macknick et al. (2012) put nuclear with towers at 0.67 gal/kWh, coal 0.48 and
     gas combined cycle 0.21.
2. **Both designs carry power plant water as large as the towers' own.**
   - Every design pays 0.44-0.62 MGD per 100 MW of IT at the power plants in Michigan, Virginia and Texas, and 0.9-1.0
     on Arizona Public Service and Salt River Project. That is the same size as, or larger than, what towers evaporate
     on site.
   - It doesn't depend on the cooling design, so it falls outside the design choice. But it belongs in any total, and
     it is the larger number in Arizona.
3. **The factors leave out hydropower reservoirs, and in Arizona that matters.**
   - The model's intensities come from EIA-923 thermoelectric cooling water. They run about half of WRI's factors, which
     include reservoir evaporation in the national average:

     | Region | Model factor | WRI 2020 | Torcellini et al. 2003 |
     |---|---|---|---|
     | PJM (Loudoun) | 0.28 | 0.63 (SRVC) | 0.06 (Virginia) |
     | MISO (Grand Rapids) | 0.31 | 0.66 (RFCM) | 0.48 (Michigan) |
     | ERCOT (Dallas) | 0.24 | 0.34 (ERCT) | 0.43 (Texas) |
     | Phoenix (APS / SRP) | about 0.50 | 1.31 (AZNM) | 7.85 (Arizona, hydro-driven) |

     All values are gal/kWh. The model's factors are [D] from the runs. Torcellini's Virginia value looks implausibly
     low.
   - Phoenix, with dry's extra 154 MWh a day per 100 MW:
     - at WRI's AZNM factor, the extra electricity costs 0.20 MGD, 34% of the towers' own;
     - at Torcellini's Arizona factor, it costs 1.2 MGD, twice the towers' own.
   - Whether reservoir evaporation belongs to electricity is disputed (Mokkapati and Das call the allocation contested;
     LBNL 2024 includes it). Design 0008 counts plant cooling water only. The Arizona comparison should be shown both
     ways (P5).
4. **The peak day.** Dry's extra grid water on the 1-in-10 peak day is 1.3-2x its average-day figure in Michigan,
   Virginia and Texas. On Salt River Project it is lower than average (0.066 against 0.079), since that utility's
   peak-day mix uses less water per MWh. The towers' own water rises by about 40%.

## 8. Proposals for Andrew

None of these is built.

**P1. Show the trade-off as three numbers (site display; no model change).**

- The package already returns everything needed: `pue_avg` and `power_mw_avg`, `power_mw_peak_1in10` and
  `power_mw_peak_day_1in10`, and `grid_<BA>_*`.
- On the cooling-systems page and in the detailed calculator, show by design and plant:
  1. extra electricity a year (%, and GWh at the campus's size);
  2. extra power in the hottest hour (MW at the campus's size);
  3. power plant water for that electricity next to the towers' own.
- This is the step in memory `cooling-tradeoff-display`. It is a UI change, so it needs Andrew's local check.

**P2. Water-cooled chillers on 90.1's curve (model; design 0015, open item 4).**

- **Problem:** the cap of 8 pins the towers' hottest hour at 1.264 everywhere.
- **Fix:** fit water-cooled chillers to 90.1's water-cooled centrifugal EIR-FT curve (PNNL-26917 Tables 78/81), as 0015
  did for air-cooled, with a sampled cap.
- **Bounds for the cap [A]:** 90.1's Path B IPLV gives COP 9.26; makers' warm-water figures run higher.
- **Expected effect:**
  - towers' hottest hour falls a few MW per 100 MW in mild wet-bulb places and varies by climate;
  - dry's hottest-hour gap grows by about the same;
  - annual changes are small.
- **Needs:** a design note, tests that close the balances, a rerun.

**P3. An outside-air evaporative design (model; new design).**

- **What it is:** air-side economizer with direct evaporative pads and chillers for rare hours, the archetype behind
  Meta's 1.08 and Amazon's statements.
- **Evidence:**
  - LBNL 2024 Fig. 4.4 (large-scale airside with adiabatic, about 1.14-1.17, WUE about 0.4 with water-cooled backup);
  - Meta's and AWS's disclosures;
  - Microsoft's Arizona fact sheet (water above 85 F, under 40% of the year).
- **Why it matters:** the public dry-against-evaporative comparison is usually against this design, and on-site water
  is far below towers'.
- **Weakest point:** it needs its own air-side physics (supply air from outside air, humidity limits). That is a larger
  change than P2, so it needs a design note first.

**P4. The base overhead against operators' disclosures (parameter; Andrew's choice).**

- **Problem:** UPS 0.90-0.99 (LBNL's range) puts towers 0.03-0.08 above disclosed evaporative fleets.
- **Options:**
  - (a) keep, and say on the methods page that the model's base sits above hyperscale fleet averages and near Uptime's
    large-site and new-build values;
  - (b) narrow UPS to 0.95-0.99 for large campuses [A], citing operators' fleet PUEs.
- **Effect of (b):** about -0.03 on every PUE, about -3 MW average and -4 MW hottest hour per 100 MW, about 3% less grid
  water. The gaps are unchanged.
- **Recommendation [judgment]:** (a) for now. The model is a planning estimate, and Crusoe's 1.2-1.4 and Uptime's 1.44
  show campuses above the hyperscale fleet averages.

**P5. Grid water with and without reservoirs (copy; no model change).**

- On the methods page and in the cooling-systems explanation, say that the power plant factors are cooling water at
  thermoelectric plants only.
- Give the hydro-inclusive comparison for Western states, where it can reverse the result (Phoenix: 34% at WRI's
  factor, more than the towers' own at Torcellini's).
- Keep design 0008's basis.

**P6. Check Arizona Public Service's marginal factor on the peak day (check).**

- **The problem:** `grid_AZPS_marginal_consumed_peak_1in10` is 6.6-7.4 MGD per 100 MW. That is about 3,000 gal per MWh
  on the peak day, against 1.0-1.1 MGD on the average day. It is the same in the model 1.11 record, so it predates 1.16.
- **Why it looks wrong:** no thermoelectric fleet consumes that much per MWh.
- **Likely cause [unverified]:** the marginal regression on hot days in a balancing authority whose load and generation
  differ by large imports.
- **Next step:** check against AZPS's EIA-930 hours before Arizona's page shows a marginal peak-day figure.

## 9. The trade-off in plain words

For the cooling-systems page and for talks with Zach Easton. The numbers are model 1.17 (updated Nov 17), shared loop,
per `runs/tables_117.md`.

> Cooling towers get rid of a data center's heat by evaporating water. Dry coolers do it with fans and outside air, and
> when the air is too warm for that they turn on chillers, compressors that run on electricity. Over a whole year the
> difference in electricity is small: a campus with dry cooling uses about 4 to 6 percent more than the same campus
> with towers in Michigan, Virginia and Texas, and about 10 percent more in Phoenix. That's because the chillers only
> run in warm weather, and the fans and pumps cost about the same either way. Published figures agree. Google's
> air-cooled campus in Nevada runs about 6 percent above its evaporative one, and Microsoft calls the increase from
> dropping evaporative cooling "nominal." The power plants' water for that extra electricity is a few percent of what
> towers would evaporate on site, so dry cooling saves nearly all of the water.
>
> The difference is at the peak. In the hottest hour of a hot summer every chiller runs, and an air-cooled chiller
> needs about twice the electricity per unit of heat that a water-cooled one needs. A 1-gigawatt campus with dry
> cooling needs about 85 to 150 megawatts more than one with towers in that hour, and that hour comes when the grid is
> already stretched. How cold the building keeps its water matters as much as the choice of design. The same dry campus
> in Dallas uses about 9 percent more electricity a year on an older chilled-water plant (7-13 C water) than on a
> modern loop at about 23 C. That's half again the gap between dry cooling and towers. Plants with warm liquid loops (30-42 C
> water) narrow the yearly gap to 2 to 7 percent.

## 10. Methods record

**This note is the long form.** No method decision is made here: the model is unchanged, and the findings in sections
1-7 stand as a check that model 1.16's dry-towers electricity holds against the evidence. When Andrew decides on the
proposals, the record follows memory `methods-notes-short-and-long`:

- **Long form:** an entry in `docs/methods/methods-log.md`. Suggested heading: "Nov 16, 2026: dry cooling's
  electricity against the evidence (check; model 1.16)", pointing here, with each decision on P2-P6 and its reason.
- **Short form:**
  - the two paragraphs in section 9 for the cooling-systems page;
  - one line for each state's methods page and brief: "Dry cooling uses 2-9% more electricity a year than towers and
    6-14% more in the hottest hour, in line with Google's, Microsoft's and LBNL's published figures; its power plant
    water is 3-13% of the towers' own".
- **Changelog:** only if P2, P3 or P4 change numbers (memory `changelog-calculations-only`).

## 11. Sources

1. Shehabi, A., Smith, S.J., Hubbard, A., Newkirk, A., Lei, N., Siddik, M.A.B., Holecek, B., Koomey, J., Masanet, E.,
   Sartor, D. (2024). *2024 United States Data Center Energy Usage Report.* LBNL-2001637. Government lab report.
   https://eta-publications.lbl.gov/sites/default/files/2024-12/lbnl-2024-united-states-data-center-energy-usage-report.pdf
   (read from https://escholarship.org/content/qt32d6m0d1/qt32d6m0d1.pdf). Tables 4.2-4.3 pp. 40-43; Fig. 4.4 p. 46;
   p. 45; p. 57.
2. Lei, N., Masanet, E. (2022). Climate- and technology-specific PUE and WUE estimations for U.S. data centers using a
   hybrid statistical and thermodynamics-based approach. *Resour. Conserv. Recycl.* 182:106323.
   doi:10.1016/j.resconrec.2022.106323. Peer-reviewed; preprint read (Research Square rs-769999, Fig. 4).
3. Lei, N., Masanet, E. (2020). Statistical analysis for predicting location-specific data center PUE and its
   improvement potential. *Energy* 201:117556. doi:10.1016/j.energy.2020.117556. Peer-reviewed; abstract only.
4. Solomon, S. (Dec 9, 2024). Sustainable by design: Next-generation datacenters consume zero water for cooling.
   Microsoft Cloud Blog. Company disclosure.
   https://www.microsoft.com/en-us/microsoft-cloud/blog/2024/12/09/sustainable-by-design-next-generation-datacenters-consume-zero-water-for-cooling/
5. Microsoft (2025). *2025 Environmental Sustainability Report*, p. 36. Company disclosure.
   https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/microsoft/msc/documents/presentations/CSR/2025-Microsoft-Environmental-Sustainability-Report.pdf
6. Microsoft (Oct 2025). *Microsoft datacenters in Arizona* (fact sheet). Company disclosure.
   https://local.microsoft.com/wp-content/uploads/2025/10/Microsoft-datacenters-in-Arizona.pdf
7. Hölzle, U. (Nov 21, 2022). Our commitment to climate-conscious data center cooling. Google. Company disclosure.
   https://blog.google/outreach-initiatives/sustainability/our-commitment-to-climate-conscious-data-center-cooling/
8. Google (2025). *2025 Environmental Report* (FY2024), pp. 108-110, endnote 166 (air-cooled sites). Company disclosure.
   https://www.gstatic.com/gumdrop/sustainability/google-2025-environmental-report.pdf ; quarterly campus PUE at
   https://datacenters.google/efficiency/ (Q1-Q2 2026).
9. Meta (Oct 2025). *2025 Environmental Data Index.* Company disclosure.
   https://sustainability.atmeta.com/wp-content/uploads/2025/10/Meta_2025-Environmental-Data-Index.pdf
10. Amazon (Jun 11, 2026). How Amazon is making its data centers more water-efficient. Company disclosure.
    https://aboutamazon.com/news/sustainability/amazon-data-center-water-usage ; Amazon (Oct 2, 2025), FAQ: Why does AI
    use water? https://sustainability.aboutamazon.com/stories/just-back-from-weftec-why-does-ai-use-water ; AWS regional
    fact sheets (PUE 2023-2025), https://sustainability.aboutamazon.com/aws-sustainability-fact-sheets/
11. Uptime Institute (2025). *Global Data Center Survey 2025.* Trade survey.
    https://datacenter.uptimeinstitute.com/rs/711-RIA-145/images/2025.Annual.Survey.Report.pdf ; Talib, R., Dietrich, J.
    (Apr 24, 2026), Dry cooling energy performance can rival evaporative cooling, UII Briefing Report 200 (summary only,
    paywalled); Dietrich, J. (Oct 24, 2024), Briefing Report 156 (summary only).
12. Crusoe (2025-2026). An inside look at the Abilene AI data center; Crusoe's 2025 Impact Report. Company disclosure.
    https://www.crusoe.ai/blog/an-inside-look-at-the-abilene-ai-data-center ;
    https://www.crusoe.ai/resources/blog/crusoes-2025-impact-report
13. Karimi, L., et al. (2022). Water-energy tradeoffs in data centers: A case study in hot-arid climates. *Resour.
    Conserv. Recycl.* 181:106194. doi:10.1016/j.resconrec.2022.106194. Peer-reviewed; abstract only.
14. Karimi, L., et al. (2025). Energy and water dynamics in data center cooling: Insights from a modeling study in
    hot-arid climates. *Appl. Therm. Eng.* 276:126802. doi:10.1016/j.applthermaleng.2025.126802. Peer-reviewed;
    abstract only.
15. Sickinger, D., Van Geet, O., Belmont, S., Carter, T., Martinez, D. (2018). *Thermosyphon Cooler Hybrid System for
    Water Savings in an Energy-Efficient HPC Data Center: Results from 24 Months and Impact on WUE.*
    NREL/TP-2C00-72196. Government lab, measured. https://www.nrel.gov/docs/fy18osti/72196.pdf
16. Vertiv (2020). *Calculating the Impact of Water Usage on Data Center Costs and Sustainability*, SL-70704. Maker
    white paper.
17. Schneider Electric (2026). White Paper 220, *Water Usage at AI Scale*, via Snider, S., TechTarget (Sep 24, 2026).
    Maker white paper, secondary.
18. ANSI/ASHRAE/IES Addendum x to Standard 90.1-2019 (2022), Table 6.8.1-3. Standard.
    https://www.ashrae.org/file%20library/technical%20resources/standards%20and%20guidelines/standards%20addenda/90_1_2019_x_20220204.pdf
    ; Table 6.8.1-7 as reproduced by Baltimore Aircoil, J22 (2015).
19. Goel, S., Rosenberg, M., Eley, C. (2017). *ANSI/ASHRAE/IES Standard 90.1-2016 Performance Rating Method Reference
    Manual.* PNNL-26917, Tables 77-83. Government lab.
    https://www.pnnl.gov/main/publications/external/technical_reports/PNNL-26917.pdf
20. Kaltra (c. 2020). *Mistral-W dry coolers*, Selection Guide 2.0. Maker catalog.
    https://kaltra.com/wp-content/uploads/2020/11/SG_Mistral-W_Ver.2.0_EN.pdf
21. Mortensen, K. (2026). *Cooling Towers Offer Water and Energy Savings as Part of Efficient Data Center Cooling
    Systems*, SPX WP-DC-26, summarizing Chiddix and Zion (Swanson Rink). Maker white paper.
    https://spxcooling.com/wp-content/uploads/WP-DC-26.pdf
22. ACHR News (Jun 9, 2014). Water-cooled technology cuts costs (analysis by Baltimore Aircoil). Trade press.
    https://www.achrnews.com/articles/126831-water-cooled-technology-cuts-costs
23. Mokkapati, V., Das, D.K. (2026). When does adiabatic cooling outperform dry cooling? engrXiv preprint, not peer
    reviewed. https://engrxiv.org/preprint/download/7795/12658/10948
24. Alston, Love, Haider (2026). Data center cooling choices shift water impacts across the grid. arXiv:2609.25437.
    Preprint. https://arxiv.org/abs/2609.25437
25. Patrizio, A. (Oct 23, 2026). Can evaporative cooling in data centers still make sense? Data Center Knowledge. Press.
26. Reig, P., Luo, T., Christensen, E., Sinistore, J. (2020). *Guidance for Calculating Water Use Embedded in Purchased
    Electricity.* WRI Working Paper, Appendix 1. NGO working paper.
    https://files.wri.org/d8/s3fs-public/guidance-calculating-water-use-embedded-purchased-electricity.pdf
27. Torcellini, P., Long, N., Judkoff, R. (2003). *Consumptive Water Use for U.S. Power Production.*
    NREL/TP-550-33905, Tables 2-3. Government lab. https://www.nrel.gov/docs/fy04osti/33905.pdf
28. Macknick, J., Newmark, R., Heath, G., Hallett, K.C. (2012). Operational water consumption and withdrawal factors
    for electricity generating technologies. *Environ. Res. Lett.* 7:045802. Peer-reviewed.
29. Siddik, M.A.B., Shehabi, A., Marston, L. (2021). The environmental footprint of data centers in the United States.
    *Environ. Res. Lett.* 16:064017. Peer-reviewed.

Not reached: the full texts of Lei and Masanet 2022 (publisher), Karimi 2022 and 2025, Uptime Briefing Report 200, and
Schneider's own white paper PDFs; makers' air-cooled chiller tables above 115 F; any grid planner's temperature
coefficient for data center load.

## 12. Reproducing

The scripts are in [cooling-power-evidence/](cooling-power-evidence/). They run with the `chiller-temperature-curve`
worktree's environment (model 1.16) and read only the ERA5 cache and the station anchors already in it.

- **`phoenix_run.py`** runs one cell's model 1.16 Monte Carlo in memory. It uses the cell, the correcting stations and
  the balancing authorities, and writes JSON:

  ```
  .venv/bin/python -B phoenix_run.py 33.50_-112.00 722780-23183,722784-03184,722785-23111+linked AZPS,SRP,WALC out.json
  ```

  It took about 4 minutes on the Mac.
- **`breakdown.py <cell> <stations> <out.json>`** gives the electricity by component at central parameters (3c).
- **`sens.py <cell> <stations>`** gives the one-at-a-time gap (3d).
- **`tables.py`** builds tables 3a, 3b and 7 from the stored cells and the Phoenix run (`runs/tables.md`).
