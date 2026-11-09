# 0007: The cooling plant inside the building, and the weather and glycol fixes that ride with it (model 1.10)

Status: **decided Nov 8, 2026 (Andrew); released in 3.14.0 (Nov 8, 2026), with every state's cells rerun and its snapshot
rebuilt.** Research behind it: the cooling-loop study of Nov 7 (primary sources with page numbers in the methods log entry of Nov 8).

## What was wrong

Through model 1.9 every campus ran supply air at 27-35 C and its liquid-cooled computers on a loop of their own at 32-45 C.
Both ranges are cited, but neither is an operating point:
- 27-35 C is the upper bound of the band Lei and Masanet's supply air floats in (their Table 3; the lower bound is 10-18 C);
- 32-45 C spans two of ASHRAE's W classes, which are ceilings the equipment must run at, each from 2 C up to its number
  (ASHRAE TC 9.9, 2021, p. 8).

So every plant was the warm-water best case, and the economizer carried most of a Michigan year. In the sensitivity analysis
at model 1.9 (West Michigan, N = 8,192), the liquid-cooled share and the liquid loop's temperature were the two largest drivers
of hybrid and assist water: total-order indices 0.48 and 0.22 for hybrid's average day.

## Decision (Andrew, Nov 8, 2026)

- The cooling plant is a choice, with each plant's ranges sampled within it.
- **The shared loop is the default.** It is the most common documented plant.
- waterledger.org's calculator shows the default.
- The detailed calculator has a picker.
- A page on waterledger.org describes the plants, with figures and citations.

On whether to include the conventional chilled-water plant: "If it's a legitimate option shouldn't we do it?" It is, so it is in.

## The plants (`physics.PLANTS`)

| Plant | Supply air | Liquid racks' water | Liquid-cooled share | Sources |
|---|---|---|---|---|
| `shared` (default): one facility water loop for air handlers and coolant units | 24-30 C [A] | the air loop's own, from the coil relation (about 16-28.5 C, centre 22.8) | 0-1 [A] | OCP "30 C Coolant" Rev 1.0 (Oct 2024) Fig. 10 p. 22; Vertiv GB200 reference designs 006, 007; Uptime Update 373 (Jun 2025): 18-24 C at the coolant units |
| `warm`: a separate warm liquid loop on its own dry coolers | 24-30 C [A] | 30-42 C [A] | 0.7-1.0 [A] | Schneider Reference Design 109 (37.2/47.2 C fluid coolers; 22.8/32.8 C chilled water for 27.8 C air); NVIDIA's 45 C rack inlet less about 3 K (OCP 2024 p. 21) |
| `chilled`: a conventional chilled-water plant | 18-22 C | the chilled water, set at 7-13 C | 0-0.2 [A] | ASHRAE TC 9.9 2021 (H1 class, recommended 18-22 C, p. 14); ASHRAE 90.4-2022 Addendum g (11 K air rise to 29 C return); 90.4's zone 5A worked example (18-19 C air, 44/56 F water); Uptime 2024 cooling survey (liquid share) |

Supply air at 24-30 C rests on these designs:
- Schneider 27.8 C;
- OCP 30 C;
- Meta's reference band, 18.3-29.4 C;
- ASHRAE's recommended upper limit, 27 C.

The 24 C floor is an assumption.

The chilled plant's air rise is 11-14 K: 90.4's 11 K basis up to Lei and Masanet's 13.9 K [A].

An air-cooled hall is not its own plant. It is the shared plant with a liquid share near 0. At West Michigan on Nov 7, an
air-cooled range (0-0.2) gave the same hybrid water as the shared loop within 1%.

### How it is built

- **`physics.plant_ranges(plant)`:** the base ranges, overlaid by the plant's.
- **`physics.with_plant(p, plant)`:** applies the link. Where the racks share the air loop (shared, chilled), `liquid_water` is
  set to `air_loop_water(p)`.
- **`physics.air_loop_water(p)`:** Lei and Masanet's coil relation, or `chilled_water` where the plant sets it.
- **The heat balance is unchanged:** it reads `liquid_water` and `air_loop_water` as before.
- **Sampling:** `sample_parameters(n, seed, plant)` and `central_parameters(plant)`. The draws share their strata across plants,
  so the plants are compared on common random numbers.
- **Running:** `cooling.run_location(..., plant=)` runs one plant; `cooling.run_plants` runs all three, the default first.
- **The BMI component** takes `plant:`. On a shared loop it refuses `liquid_water`, and outside the chilled plant it refuses
  `chilled_water`.

### Known limits

- **The warm plant has one switch point.** In the warm plant the hybrid and assist switch point is one setting for the whole
  plant, the two loops' limits weighted by their heat (`loop_limit`). A real plant could switch each loop's coolers on its
  own [A].
- **The chilled plant's coils are taken as dry.** At its water temperature the room coils can condense some indoor moisture,
  which humidifiers then replace. The model doesn't count that water [A].
- **Not modeled:**
  - direct evaporative cooling of outside air (a heat rejection design of its own);
  - heat reuse;
  - immersion cooling as such (it runs at or above the warm loop's temperatures).

## The weather fix: map the dew point, not the depression (qm-3)

- **What was wrong:** qm-1 and qm-2 mapped temperature and the dew-point depression separately, so a hot-day temperature
  correction carried the dew point up with it.
- **Evidence:** at model 1.9's checked places, corrected peak days ran humid against their stations, by 0.72 C of wet bulb in
  Michigan and 0.35 C in Ohio. That is about 37 more hours a year above a 22 C wet bulb.
- **The fix:** qm-3 maps T and Td each by its own quantiles, with Td kept at or below T.
- **Result:** in a scratch test on the same places, the error fell to 0.23 C in both states.
- **What it doesn't fix:** hybrid's peak-day lean of 4-6% is not explained by this; its cause is still open.
- **Lapse rate:** the lapse rate moves temperature only. The dew point is not lapse-adjusted [A].
- **Cache:** station fits are cached by what they fit (`quantile_mapping.FIT`), so a T-D fit is never read as a T-Td one.
- **The check gains W7:** the mean error in the 1-in-10-year peak day's mean wet bulb on corrected cells, at most 0.5 C [A].
  qm-2 would fail it in Michigan.

## The glycol (model 1.10)

- **Through model 1.9:** the dry coolers' glycol loop (model 1.9) used water's heat capacity and density.
- **Now:** propylene glycol at 30-40% by volume [A], with heat capacity and density at 20 C between Dow's 30% and 40% tables
  (DOWFROST Technical Data Sheet, Form No. 180-01314-1019): 3.870 and 3.701 kJ/kg/K, 1,025.2 and 1,036.9 kg/m3.
- **Why 30-40%:** Dow's freezing points are -12.7 and -21.1 C, the span from burst to freeze protection in a Great Lakes winter.
- **Not modeled:** glycol's higher viscosity would also add pump pressure [A].
- **Effect:** more pump power in the dry plant's economizer hours. A dry plant now takes 0.07-0.2% more electricity than
  towers in freezing hours, where it took about the same.

## Tests

- **`tests/test_plants.py`:**
  - each plant's ranges and link;
  - the chilled plant's set water;
  - every design's electricity ordered warm < shared < chilled;
  - Dow's glycol values;
  - the BMI's guards;
  - the plant carried from runs to a cell record to an estimate.
- **`test_balances`:** mass and energy close for every design in every plant.
- **`test_physics_properties`:** each plant's draws fill their strata.
- **`test_quantile_mapping`:**
  - a hot-day correction leaves the dew point alone;
  - the lapse rate moves temperature only.
- **`test_era5_check`:** W7.
