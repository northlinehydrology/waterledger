# 0009: Battery cell plants, the second water user

Status: **decided Nov 9, 2026 (Andrew; answers and decisions at the end). Built on branch battery-plant-model, not released.** Evidence: `docs/research/battery-plant-water.md`
(primary sources with page numbers). Cathode materials plants are a separate model with their own note (0012, to follow).

## What and why

Andrew (Nov 9, 2026) chose battery manufacturing as the next water user after data centers, built as two models:
- cell plants, the "gigafactories" that turn electrode materials into finished cells;
- cathode materials plants, which make the cathode powder.

This note covers cell plants. Grid battery storage is not a water user; it will come later as part of the grid component (0008).

Michigan's cases:
- Ultium (now LG Energy Solution) in Delta Township: 1.5-1.7 MGD projected, 0.56 MGD to sewer (DOE/EA-2189-S1, p. 13).
- Ford BlueOval Battery Park in Marshall: no plant figure, but a 10.5 MGD pump station was built for the campus.
- LG Energy Solution in Holland.

The calculator is a what-if tool, like the data center one. A proposal with no water figure can be run as a scenario. A
real plant's own numbers belong in a paid study.

## What the evidence says

- **Withdrawal.** Six U.S. cell plants' DOE environmental assessments project **27,000-39,000 gal/day per GWh/yr** of
  capacity, at full output. CATL's company-wide 2025 figure and three Hungarian plants fall in the same band.
- **Consumption.** 63-76% of withdrawal is consumed where both supply and discharge are given (Lansing 63-67%, BlueOval
  SK 72.5%, CATL 65%, LGES 76%). Only evaporation can account for that much at that scale.
- **What uses the water.** Spring Hill's EA names cooling-tower make-up as "the most water intensive process"
  (DOE/EA-2189, p. 14). The heat comes from:
  - electrode drying ovens and NMP solvent recovery;
  - dry-room air handling;
  - formation and aging (the first charge and discharge cycles);
  - compressors.

  Process water (purified water for anode slurry, boiler make-up, scrubbers) and staff water are the rest.
- **Peak.** Spring Hill gives 1.4 MGD average and 1.85 MGD peak (ratio 1.32).
- **Gaps.**
  - Every figure is a projection made before construction; nothing measured is public.
  - Nothing public splits cooling from process water.
  - There are no seasonal series.

  The model uses defensible ranges where a number is missing, and the sampling carries the uncertainty (Andrew, Nov 9).

## Approach: a heat balance, like the data center model

Water follows heat. The energy balance closes on the evidence: plants use about 30-35 kWh of energy per kWh of cells
(Kuki et al. 2025, gate-to-gate). If half to three quarters of that leaves through cooling towers, evaporation at
about 1.48 L per kWh of heat gives 22-39 L/kWh. That brackets the 27-38 L/kWh the plants report as consumed. A
worked check at Lansing's projected size (43.75 GWh/yr):

| Step | Value |
|---|---|
| Cells made, at full output | 43.75e6 kWh/yr ÷ 8,760 h = 4,990 kWh/h |
| Plant energy at 32 kWh per kWh [A] | 160 MW |
| Heat to the cooling water at 0.65 [A] | 104 MW |
| Evaporation at 1.48 L/kWh | 154 m³/h = 0.98 MGD |
| Blowdown and drift at 5 cycles [A] | 0.98 ÷ 4 = 0.24 MGD |
| Process and staff water [A] | about 0.3 MGD |
| **Withdrawal** | **about 1.5 MGD** (EA: 1.5-1.7) |
| Consumed | about 1.0-1.1 MGD, 67-72% (EA: 63-67%) |

So the model is built from the plant's heat, not from a gallons-per-GWh factor. The factor would have no weather, no
cooling design, no electricity and nothing to sample.

### Hour by hour

For each hour of the cell's weather (the same ERA5 hours the data center model runs on):

1. **Production** = capacity × utilization ÷ 8,760, in kWh of cells per hour.
2. **Plant energy** = production × energy intensity, split into electricity and fuel (natural gas for drying ovens,
   boilers and thermal oil heaters).
3. **Heat to the cooling water**, in two parts:
   - **Process heat:** a share of plant energy, steady through the year.
   - **Outdoor air load:** the dry rooms and clean areas take in make-up air that must be cooled and dried to a very low
     dew point. That load follows the outdoor air's enthalpy above the supply condition, so it rises in humid summers.
     It is sized as a share of the cooling load at the location's design condition, so it scales with the plant.

   The chillers add their compressor work: heat rejected = cooling load × (1 + 1/COP).
4. **Heat rejection**, using the existing tower physics:
   - evaporation = heat × wet share × the Rutberg et al. (2011) evaporative ratio ÷ latent heat;
   - drift;
   - blowdown + drift = evaporation ÷ (cycles − 1).

   Three designs:
   - `towers`: open towers all year, which most EAs describe;
   - `hybrid`: dry most of the year, evaporative in warm weather;
   - `dry`: air-cooled chillers, as at KORE Power.

   The `assist` and `lake` designs belong to data centers and are left out.
5. **Process water:**
   - purified water for anode slurry, evaporated in the dryers: consumed;
   - reverse osmosis reject and boiler blowdown: returned;
   - water leaving in recovered NMP by tanker: consumed for the watershed;
   - boiler make-up.

   These are per kWh of cells [A], from the EA tables (A123's Table 2-5 gives the streams by name) and checked against
   the totals.
6. **Staff water** follows the people on site, as for data centers:
   - Lansing's EA gives 1,522 employees (about 35 per GWh/yr);
   - Spring Hill's gives 1,300.

**Outputs**, the same shape as the data center's:
- withdrawn, consumed and returned;
- the average day and the 1-in-10-year peak day, as percentiles;
- electricity, average and peak;
- power plant water through the grid component.

Results are reported per 10 GWh/yr of capacity and scaled to the plant's size. Fuel burned on site has no water at the
grid. Upstream water for gas is outside the scope (campus plus power plants).

**Mass and energy close, held to it by tests:**
- withdrawn + condensate = consumed + returned;
- plant energy in = heat to the cooling water + heat to exhaust air and flue gas + compressor work accounted.

### Parameters to set [A]

Each is sampled in a range with a source or a stated reason. Before the ranges are fixed, a deep dive will read the
energy studies of cell production that the research did not get through, starting with the GREET battery documents.

| Parameter | Starting range | Basis |
|---|---|---|
| Energy per kWh of cells | 25-45 kWh/kWh | Kuki et al. 2025 (30-35); published estimates to be read |
| Electricity share of plant energy | to set | SK Bartow's air permit lists the gas equipment; EA utility figures |
| Share of plant energy to the cooling water | 0.5-0.8 | the energy balance above; to be narrowed by the deep dive |
| Outdoor air share of design cooling load | 0.1-0.4 | dry-room HVAC references, to find |
| Chiller COP | data center ranges | shared with the data center model |
| Cycles of concentration, drift, evaporative ratio | data center ranges | shared |
| Process water per kWh, by stream | to set | EA tables (A123, Lansing, BlueOval SK) |
| Staff per GWh/yr, gal per person per day | 25-40; data center range | the EAs' employment figures |
| Utilization (output ÷ nameplate) | see question 2 | — |

**Check, not fit.** At full output, the central estimate at each EA plant's own location should fall in that plant's
projected range:
- Lansing, Spring Hill, Stanton, Glendale and Kokomo;
- Buckeye with the dry design.

The peak-day ratio should be near Spring Hill's 1.32. A sensitivity analysis on a Michigan cell, as for model 1.9,
says which parameters drive the result.

## How it fits the packages

- **`waterledger-models`:** a new `battery/` package beside `datacenter/`, with `physics.py`, `plant.py` (the run) and
  `bmi.py` (`BatteryCellBmi`, on the same `ScalarPointBmi` base as `CoolingWaterBmi`). Basin Ledger can couple it like
  the data center component.
- **Shared heat rejection.** The tower, hybrid and dry-cooler physics now sits inside `datacenter/physics.py`. It moves
  to a shared module both models import. Every data center result must stay identical, held by an identity test, as
  with the grid change in 1.11.
- **`waterledger`:**
  - `BatteryCellPlant(Facility)` with `kind="battery_cells"`, `capacity_gwh`, `cooling` (`towers`, `hybrid`, `dry`) and
    an optional `chemistry` (`nmc` for NMC and NCA, or `lfp`; see "Chemistry, revised" below);
  - `Site.estimate()` dispatches on the facility.

  Site and Estimate still assume a data center in a few places (for example `it_mw` in the site's BMI config). Those
  are fixed so neither changes shape when a type is added (0001).
- **Cell runs and snapshots.** Precomputed per ERA5 cell, like the data center results, so the site reads them without
  running Python. The battery run is a simpler heat balance with no economizer or air loops, so it should add minutes,
  not hours, to a state's run; that will be measured on one state first. Results are keyed per 10 GWh/yr, beside the
  data center's per 100 MW.
- **Release.** Model 1.12 in a minor release, with READMEs, methods log and CHANGELOG checked before release. The
  website follows in its own step. The calculator page for battery plants is a UI change and needs Andrew's local check.

## Questions for Andrew

1. **Shared heat rejection module.** Move the tower, hybrid and dry-cooler code out of `datacenter/` so both models use
   one copy, with data center results held identical? Recommended. The other way is a second copy that can drift.
2. **Utilization.** Default at full output, the way every EA states its figure, with a utilization range sampled for
   plants running below nameplate? Recommended: full output as the headline; a range of about 0.6-1.0 [A] to be
   sourced, since new plants ramp up for years.
3. **Unit.** Per GWh/yr of cell capacity, the unit announcements and EAs use? The alternative is plant power in MW,
   which most proposals don't state.
4. **Designs.** Towers, hybrid and dry only?
5. **Order.** Package and tests first, then the cell runs for Michigan, then the other states, then the site. Or the
   package first and the site's display decided later, as with grid water?


## Answers From Andrew
1. Interesting, and yes we want modular code. I think I see where its going, for industrail operators, there will be a"components" or similar thing that different types of users can share. the only reason to keep them seprate is if, for example a cooling tower at a data center != a cooling tower at the battery cell plant in some fundemental way. Its sounds like no, they are the same and should be made modular. 
2. I agree with the untilization estimate plan
3. Unit, like, is this the, "how big is the plant" estimate, if so we should go with industry conventions, if plants are reported in GWh / yr, then we should use that too. We can take care of all the math behind it obviously. We dont need to "normalize" everything to plant power in MW because data centers are, but we do need to make all the calcs we need. Stating a size in industry standard, useful, understandable way is good though.
4. for designs beyond those should we inlcude lake / stream water cooling? 
5. Package first, site decided later (we also may wait on adding battery plants to water ledger for a while, im not sure)

### Follow-up on question 4: lake or stream cooling

- **Lake (once-through from a Great Lake):** recommended as a fourth design, through the shared heat rejection code
  that the data center `lake` design already uses (the withdrawal follows from heat and temperature rise; forced
  evaporation follows Diehl et al. 2013).
  - No battery plant in the evidence uses once-through cooling.
  - At Lansing's size it would need roughly 100 MGD at a 10 F rise.
  - A new plant that size falls under 40 CFR 125.81 (over 2 MGD design intake, at least 25% for cooling). The new-facility
    rule then holds its intake to about what closed-cycle cooling would take.
  - As with data centers, the number is shown true to the physics and the rule is a flagged note. The design shows why
    plants use towers, and covers a plant sited on a Great Lake (Holland is near Lake Michigan).
  - It costs little once the heat rejection code is shared.
- **Stream (once-through from a river):** not recommended in the package. Whether a river can take the heat depends on
  its low flow and the state's temperature limits at that reach. That is a coupled question for Basin Ledger, the same
  one as Saline Township's proposed discharge.

## Decisions (Nov 9, 2026)

1. **Shared components.** The cooling tower, hybrid, dry-cooler and lake physics move to a shared module both water
   users import. A tower is a tower: the physics depends on heat, weather and the tower's settings, not on what makes
   the heat. Each user model keeps only what is its own: its heat and power, staff and process water. Every data
   center result stays identical, held by an identity test.
2. **Utilization.** Full output is the headline, the way every EA states its figure. A sourced utilization range of
   about 0.6-1.0 [A] is sampled for plants below nameplate.
3. **Size in the industry's unit.** A plant is stated in GWh/yr of cells. The package does whatever conversions the
   calculation needs internally. Nothing is restated as MW to match data centers.
4. **Designs.** Towers, hybrid, dry and lake (Andrew, Nov 9: yes to lake). Stream once-through is left to Basin Ledger.
5. **Order.** Package first. Whether and when battery plants go on waterledger.org is decided later.
6. **Operating settings are each user's own (Andrew, Nov 9).** The tower physics stays shared, but what an operator
   chooses is not equipment: cycles of concentration and the hybrid's switch margin are set by each water user model
   from its own evidence (`heat_rejection.OPERATING`). Both take 3-6 cycles for now (Andrew, Nov 9): Lansing's EA
   implies about 3, and SK Bartow's 8 is only an air permit's drift assumption, so the battery documents don't
   support a different range. Cycles depend mostly on source water, a matter of place; setting them from the
   place's water quality for every user is a later design question. Where a plant's own documents give a setting,
   a run fixes it (`plant.run_location(..., settings={"coc": 3.0})`).
7. **Sampled, set or input (Andrew, Nov 9).** Not every parameter has to be sampled. Each has a role: sampled
   (uncertain, and it moves the results), set (one value with its source, overridable by a plant's documents or a
   scenario), or input (a fact about the plant or place: size, design, chemistry, water reuse, later source water).
   The sensitivity analysis moves parameters from sampled to set. A set parameter keeps its source and stays in
   the methods.

## Chemistry, revised (Nov 10, 2026; for Andrew to agree)

The note first said chemistry would be recorded with no effect, because the EAs show no difference. But every EA plant
with a figure makes nickel cells (NMC at BlueOval SK, NCA at StarPlus, NMC slurry at Ultium), so the EAs cannot show
one. Ford's Marshall plant, a Michigan case, makes LFP cells. The physics does show a difference: Degen et al. (2023)
find the same energy per m² of electrode for every chemistry, and LFP needs about 1.67 times the electrode area per kWh
(37.5 kWh/kWh against 22.4 for NMC811). Large LFP prismatic cells with thicker electrodes narrow that.

So `chemistry="lfp"` samples an `lfp_factor` of 1.2-1.7 [A] on the plant's energy per kWh, and its heat and cooling
water follow. The anode slurry water stays as NMC's [A], about 1% of the plant's water. An NMC plant's draws are
unchanged. At West Michigan weather the median withdrawal of a 43.75 GWh/yr towers plant goes from 1.05 to 1.46 MGD (about 40%). No LFP
plant has a public water figure to check it against; that gap is stated. Dropping the factor (back to recorded only)
is one commit to revert.

## Check at Lansing after decisions 4, 6 and 7 (Nov 9, 2026)

West Michigan weather (2023-2024), 43.75 GWh/yr at full output, towers, 200 draws, p10 / p50 / p90 in MGD. The EA
figures are projections (DOE/EA-2189-S1, p. 19).

| Run | Withdrawn | Consumed | Returned |
|---|---|---|---|
| Cycles 3-6 (the shared range) | 0.80 / 1.07 / 1.38 | 0.58 / 0.78 / 1.01 | 0.20 / 0.28 / 0.40 |
| Lansing's own cycles, 3 | 0.92 / 1.19 / 1.55 | 0.58 / 0.78 / 1.01 | 0.33 / 0.42 / 0.54 |
| EA | 1.5-1.7 | 0.94-1.14 | 0.56 |
| Lake design, Lake Michigan temperatures | 45 / 64 / 92 | 0.37 / 0.49 / 0.62 (forced evaporation) | the rest |

With Lansing's own cycles the discharge reaches the EA's at p90, and withdrawal reaches the EA's low end at p90.
What is left is consumption, about 20% low at the median. That is the evaporative ratio below 1 (Rutberg et al.
2011; the shared `er_adj`), the model's stated departure for every user: with all the heat evaporated, the central
case gives 1.01 MGD (`docs/research/battery-cell-parameters.md`, sec. 8). Nothing was tuned to the EA.

The lake design draws about 60 times what towers do and evaporates about two thirds as much. At this size it falls
under 40 CFR 125.81; the number is shown true to the physics and the rule as a flagged note.

## Check at every EA plant (Nov 10, 2026)

Each plant at its own location (Open-Meteo hourly weather, 2015-2024) and size, towers, NMC, full output, 200 draws,
p10-p90 (median) in MGD against its EA's projection. Reproduced by `examples/battery_cell_plants_ea_check.py`.
Nothing was tuned to these.

| Plant | GWh/yr | Withdrawn | Consumed | To sewer |
|---|---|---|---|---|
| BlueOval SK, Stanton, TN | 45 | 0.89-1.56 (1.20); EA 1.2 | 0.65-1.13 (0.87); EA 0.87 | 0.22-0.44 (0.30); EA 0.33 |
| BlueOval SK, Glendale, KY | 82 | 1.59-2.73 (2.11); EA 2.4 | 1.14-1.99 (1.54); EA 1.74 | 0.39-0.78 (0.54); EA 0.66 |
| Ultium, Spring Hill, TN | 50 [A] | 0.98-1.70 (1.31); EA 1.4 | | |
| Ultium, Spring Hill, peak day | 50 [A] | 1.23-2.22 (1.66); EA 1.85 | | |
| StarPlus, Kokomo, IN, maximum against the peak day | 67 | 1.65-3.00 (2.23); EA 2.59 | | |
| KORE Power, Buckeye, AZ | 12 | 0.25-0.43 (0.33); EA 0.45 | | |
| Ultium, Delta Twp (Lansing), MI | 43.75 | 0.80-1.38 (1.06); EA 1.5-1.7 | 0.58-1.01 (0.78); EA 0.94-1.14 | 0.20-0.40 (0.27); EA 0.56 |

- **Four of the six fall inside the model's range** (Stanton, Glendale, Spring Hill, Kokomo), and Stanton's three
  figures sit on its medians. Buckeye is just above the range, Lansing well above it.
- **Lansing is the outlier, not the rule.** Its EA projects the most water per GWh/yr of any plant (34,300-38,900 gpd
  against Stanton's 26,700 and Glendale's 29,300). With its own 3 cycles it reaches the EA at p90 (above). So the
  "consumption about 20% low" read from Lansing alone was about Lansing's projection, not a bias in the model: at
  Stanton and Glendale the consumed share matches. The evaporative ratio below 1 stays a stated departure.
- **Spring Hill's size is not in its EA.** At GM's 50 GWh/yr (unverified) the median is 6% below the EA; at 35 GWh/yr
  it would be 35% below. Its peak-to-average ratio, 1.32, against the model's 1.27-1.37 across these plants, is the
  one check of the peak day.
- **Buckeye was to be the dry check, and it isn't one.** "Closed-loop chiller water" describes the chilled loop, not
  how the heat leaves: the dry design gives 0.05 MGD, a tenth of the 0.45 projected, while towers come just short of it at p90 (0.43). The
  figure is an allocation for an unstated phase in the desert, so it neither confirms towers nor tests dry. There is
  no public check of the dry design.
- **Kokomo's** 2.59 MGD is a maximum, and its EA's own two numbers disagree (3,300 gpm is 4.75 MGD). Against the
  model's 1-in-10-year peak day it falls inside the range.
