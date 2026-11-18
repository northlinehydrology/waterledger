# 0022: Outside air with evaporative pads, a fifth design (model 1.17)

Status: **decided Nov 17, 2026 (Andrew: the four choices below accepted as built). Merged in model 1.17 (#28); not released, and
not on waterledger.org's design buttons until Andrew has checked it locally (his choice, Nov 16).** Proposal P3 of the dry-cooling evidence note
(`docs/research/cooling-power-evidence.md`, branch `cooling-power-evidence`, sections 5f and 8).

## Why

The model's four designs all cool the halls through a facility water loop (`cooling.py`: "A direct outside-air design would use
far more air and is not modeled"; 0007). The design the largest operators describe is different:

- outside air is drawn straight into the halls;
- it is cooled by wetted media on hot days;
- it is mixed with return air on cold days;
- chillers, if there are any, run in the rare hours the air can't do it.

| Who | What they publish | Type |
|---|---|---|
| Meta | Direct evaporative cooling; fleet PUE 1.08, WUE 0.19 L/kWh withdrawn per IT kWh (2024) | operator disclosure |
| Amazon | Free air "about 90% of the time"; water only above "roughly 85 F"; chillers would take "25% to 35% more electricity" on those days (Jun 2026); fleet PUE 1.14, WUE 0.12 (2025); Ohio 1.12 / 0.06, N. California 1.18 / 0.39 | operator disclosure |
| Microsoft | Arizona's direct evaporative cooling takes water "when the temperature exceeds 85°F" and "less than 40% of the year" (Oct 2025 fact sheet) | operator disclosure |
| LBNL 2024 (Shehabi et al.), Fig. 4.4 | Large-scale "airside economizer + adiabatic", simulated over 965 TMY stations: PUE about 1.17 (1.13-1.21) with air-cooled chiller backup, 1.14 (1.11-1.18) with water-cooled; WUE about 0.4 L/kWh with water-cooled backup; "Some hyperscale facilities report WUE values for similar systems of 0.1-0.3 L/kWh" | national lab report |

Most public "dry cooling costs more electricity" comparisons are against this design, not against towers. It is also the design
behind the operator switch setting (0016), which the model already samples. Without it, Water Ledger can't answer the question
people actually ask.

## The design

Code `outside_air`. Label, by how heat leaves (Andrew, Nov 15): **"Outside air into the halls, with evaporative pads on hot
days"**. Each hour, per kW of IT:

**Air flow.** The halls' air flow is set by the computers' air rise (`air_rise`, 13.9-19.4 K; the shared plant's): m = room heat /
(cp x rise), the flow the existing air handlers carry. Fans move it at the air handlers' pressure (`crah_pa`, 300-700 Pa) [A]:
- outside-air units add filters and media where hall coolers have coils;
- no published pressure for large campuses was found.

**Three regimes**, by the outside dry-bulb t against the supply air floor T_s (`supply_air`, the plant's) and the operator's setting
S (`switch_setting`, 26.5-32 C, 0016; at least T_s):

1. **Cold, t < T_s: outside air mixed with return air** to T_s.
   - Outside air's share of the supply: f = (T_r - T_s) / (T_r - t), with T_r = T_s + rise. The rest is return air.
   - The exhaust carries the heat.
   - Humidifiers make up their sampled share (`humidify_share`) of any shortfall below the low dew-point limit (-9 C) in the outside
     air taken, as the other designs do for their ventilation air.
   - No other water.
2. **Mild, T_s <= t <= S: all outside air, supply at t.**
   - The supply floats with the weather up to the operator's setting, as the fleets above run.
   - No cooling water.
3. **Hot, t > S: pads.**
   - Media with saturation effectiveness e (`assist_eff`, 0.70-0.80, the same media as assist's) cool the air toward its wet-bulb:
     T_p = t - e x (t - t_wb).
   - How far the pads go once they are on is sampled (`pad_full`, 0-1) [A]:
     - 0: throttled to reach S and no lower, as staged or modulated media can hold a setting;
     - 1: the media's full effect, down to T_s at most, as on-off media do;
     - no operator publishes which.
   - At Phoenix's cell, with all-air-cooled halls at central parameters, the ends give 0.18 and 0.37 L evaporated per IT kWh.
   - Water evaporated = m x cp x (cooling by the pads) / L, from the adiabatic balance: the air's sensible heat goes into the water's
     latent heat.
   - Bleed is the pads' sampled share (`assist_bleed`).
   - Where T_p > S (humid heat), **trim chillers** cool the air the rest of the way: load = m x cp x (T_p - S).
     - They are air-cooled (0015's form, condenser on outside air at t + 12), with a chilled-water pump. That matches how heat leaves
       in this design: by air [A].
     - Coil water is S less the air coil's approach, as `air_loop_water` works it out.

**Liquid-cooled racks.**
- The share of heat that goes to liquid (`liquid_share`, `liquid_air_share`) is rejected through the plant's liquid loop on dry
  coolers, with air-cooled chillers when needed: the dry design's loop, at `liquid_water`.
- So the plant variants (shared, warm, chilled) keep their meaning: supply air floor, liquid share and liquid water.
- The chilled plant's 18-22 C supply air is a low floor for outside air, so that variant mixes return air most of the year.
- **Liquid racks cost this design power in warm hours.** It is the only design where they do. Outside air cools air-cooled halls
  with no chillers up to the operator's setting. Liquid racks on the shared plant's 16-28.5 C loop water need dry coolers, and
  chillers once the air is warmer than that water allows. A campus that pairs outside-air halls with liquid racks would more likely
  run them warm, as the warm plant does. The plant variant decides that here.
  - This is why the evidence checks below are given both all air-cooled (the disclosed fleets) and at the plant's sampled liquid
    share.

**Not modeled [A]:**
- dehumidifying outside air. Fleets running this design accept humid supply air (Meta's specification allows up to 90% relative
  humidity), and no published dehumidification load exists for them;
- separate pad pumps and the media's own pressure drop (under 100 Pa, inside `crah_pa`'s range);
- ventilation air as a separate flow (`oa_cfm_per_mw`): it is part of the outside air here.

## Balances (tests)

- **Air, every hour:** the hall air carries the room heat. Mixing closes: f x t + (1 - f) x T_r = T_s.
- **Evaporation:** m x cp x (cooling by the pads) = evaporated mass x latent heat. Pad water never exceeds what saturating the air at
  its wet-bulb would take.
- **Energy:** facility power = IT + losses + fans + trim chillers + their pump + the liquid loop's chillers, pumps and fans. Every
  kW of it, plus the outside air's heat, leaves in the exhaust air and the chillers' condensers.
- **Mass:** withdrawn + condensate = consumed + returned, as for every design.
- **Bounds:**
  - no cooling water at or below S;
  - the supply between T_s and S;
  - pads never below the wet-bulb;
  - PUE at least 1.
- **Water against towers:** no more than towers at the same hour and draw, except in hours hotter than the halls' return air
  at the supply floor (T_s + rise).
  - In those hours, pads cooling all the outside air can take more than the IT heat would evaporate in a tower, so in very dry heat
    this design can use more than towers.
  - In the test grid (5% relative humidity) that happens above about 43 C on the shared plant, and above about 33 C on the chilled
    plant, whose floor is 18-22 C.
  - That is physics, kept and stated, not capped (memory: estimates true to physics).
  - A real plant might raise its supply temperature in those hours instead. The model doesn't.

## Water limits, source and wastewater rules

- **Under a water limit (0006)** the pads' evaporation is cut by `wet_frac` and the trim chillers carry the rest, as with assist.
- **Source and wastewater (`EVAPORATIVE`)** stay towers and hybrid. This design's water is pad evaporation and small bleed, like
  assist's [A].

## Checks against the evidence

At model 1.17 in memory (Grand Rapids, Loudoun County, Dallas, Phoenix; 400 draws; shared plant; p50):

The same draws for dry and towers, and both tables with the 10th-90th percentiles, are in
`docs/methods/outside-air-check/check.md`. Medians, all air-cooled halls, against the shared plant's dry and towers at the plant's
liquid share:

| Place | Outside air: PUE a year / hottest hour | WUE withdrawn, L/kWh | Hours on pads | Dry: PUE / hottest hour | Towers: PUE / hottest hour / WUE withdrawn |
|---|---|---|---|---|---|
| Grand Rapids | 1.107 / 1.115 | 0.01 | 1% | 1.175 / 1.340 | 1.134 / 1.256 / 1.61 |
| Loudoun County | 1.107 / 1.112 | 0.01 | 4% | 1.192 / 1.352 | 1.142 / 1.254 / 1.66 |
| Dallas | 1.107 / 1.124 | 0.08 | 15% | 1.233 / 1.377 | 1.163 / 1.257 / 1.78 |
| Phoenix | 1.107 / 1.119 | 0.25 | 32% | 1.257 / 1.403 | 1.144 / 1.255 / 1.82 |

**Against the evidence.**
- **Hours on water** match what the operators say:
  - Phoenix 32% (26-39%) against Microsoft's "less than 40% of the year" in Arizona;
  - Loudoun 4% and Dallas 15% against Amazon's "about 90% of the time" without water across its fleet.
- **PUE.** 1.107 with all-air halls sits between Meta's fleet 1.08 and AWS's 1.12-1.18 by region. It is below LBNL's modeled
  1.14-1.17, which has chillers at the base and a higher base overhead.
  - It barely moves with climate, because the halls' fans move a fixed flow and the trim chillers run under 1% of hours at p50.
  - The base overhead (UPS and distribution, 1.09 at the middle) is most of it, as the evidence note's P4 says.
- **Water, Phoenix.** 0.25 L withdrawn per IT kWh (0.17-0.38) sits:
  - between AWS's fleet (0.12) and its Northern California region (0.39);
  - near LBNL's modeled 0.4 and Meta's 0.19.
- **Water, the other three places** are near zero, as AWS's Ohio and Virginia 0.06 are.
- **What it doesn't match: Microsoft's Arizona figures.**
  - The figures are WUE 1.63 (2024) and 2.24 (2022). Both are from search snippets and fact sheets that now return 404, so they are
    unverified.
  - If right, they are six to nine times the model's. They may count other water: pad bleed at Arizona's high dissolved solids,
    reverse osmosis reject, or humidification.
  - The model's bleed (`assist_bleed`, 0-0.5) and pad control (`pad_full`) don't reach them.
  - Not resolved. A verified Microsoft per-site figure would settle it.
- **Liquid racks.** At the plant's sampled liquid share the design's PUE rises to 1.12-1.15 and its hottest hour to about 1.21: the
  liquid racks' dry loop needs chillers in warm hours (above).
  - Its year is still below towers' at three places but not in Phoenix (1.150 against 1.144).
  - Its hottest hour stays below towers' everywhere (1.19-1.21 against 1.25-1.26).
- **The trade-off.** With air-cooled halls, on these numbers the outside air design beats towers on both water and electricity
  everywhere. It beats dry (at the plant's liquid share) on electricity by 0.07-0.15 a year and 0.22-0.28 in the hottest hour. That is why operators who can build it do. Its limits
  are the ones it doesn't model:
  - humid supply air;
  - filtration near smoke and dust;
  - the halls' size and air paths.
  It also can't serve most liquid-cooled AI racks without a water loop.

## What it touches

- **Model code:**
  - `heat_rejection.outside_air`, new: the regimes, water and trim load;
  - `datacenter/physics.py`: `DESIGNS`, `hourly_heat_power`, `_rate_parts`, `hourly_limited`, `blowdown_temperature`;
  - `datacenter/kernel.py`: design code 4 and its fields;
  - `datacenter/cooling.py`: `DESIGNS`, `LABELS` and the closed-loop text.
- **The waterledger package:**
  - `facilities/data_center.py` and `scenario.py` labels;
  - `national/build.py` checks.
- **Tests and records.**
- **Cell runs:** every state, about 25% longer per cell.
- **Not touched:**
  - battery plants: a cell plant's dry rooms aren't hall air;
  - `scenario.DESIGNS`' default list, and waterledger.org's buttons.

## Decided (Andrew, Nov 17, 2026: all four as built)

1. The label and code name.
2. Air-cooled trim chillers, not water-cooled (LBNL models both; Meta runs none). Water-cooled would add tower water in the hottest
   hours.
3. The supply floats to S before the pads come on, rather than holding T_s. Once on, how far the pads go is sampled (`pad_full`,
   0-1). Choosing one end would halve or double the design's water.
4. Humid supply air accepted rather than dehumidified.
