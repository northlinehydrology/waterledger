# Water for a large user's power supply: new gas plants, solar and wind

Research note, Nov 10, 2026. Evidence base for power supply scenarios in the waterledger packages: what serves a large
water user's hourly electricity (the existing grid, new gas plants on or near the site, new solar and wind under a power
purchase agreement, or a mix), and the water each takes. Public sources only. No code. The design is proposed in
`docs/design/0014-power-supply-scenarios.md`.

Scope rule, the same as design 0008's boundary: every plant here is a hypothetical, modeled from public data. No real
power plant, transmission line, substation or route is named, profiled or laid out. Real plants' reported data (EIA-923
and EIA-860) are used only in aggregate, to check per-MWh factors, never to describe a plant.

Conventions:

- **Withdrawal**: water taken from a source. **Consumption**: water not returned (evaporated, or carried off in product
  or waste). For dry cooling, PV and wind the sources set withdrawal equal to consumption.
- All factors are per MWh of **net** generation unless stated. 1 gpm/MW = 60 gal/MWh. 1 L/kWh = 264.2 gal/MWh.
  1 acre-foot (AF) = 325,851 gal.
- **Status**: *review* (a compilation of published estimates), *model* (a design study or heat-budget model),
  *reported* (agency totals of plant reports, used here only in aggregate), *derived* (my arithmetic from the cited
  inputs, marked **[A]** where an assumption enters).
- Page numbers are the printed page numbers unless marked "PDF p.".
- **UNVERIFIED** marks a figure taken from a search result or secondary source that I could not check against the
  primary document in this session.

## 1. Figures

### 1a. Natural gas combined cycle, by cooling type

| # | Cooling | Consumption, gal/MWh | Withdrawal, gal/MWh | Source | Status |
|---|---|---|---|---|---|
| G1 | Towers | median 205 (130-300), n = 6 | median 255 (150-283), n = 7 | Macknick et al. (2012), ERL 7:045802, Table 2 p. 6, Table 3 p. 7 | review |
| G2 | Towers | median 198 (130-300), n = 5 | median 253 (150-283), n = 6 | Macknick et al. (2011), NREL/TP-6A20-50900, Table 2 p. 13, Table 3 p. 14 (the 2012 paper revises these slightly) | review |
| G3 | Towers | median 210 (47-300), n = 19 | median 250 (150-760), n = 16 | Meldrum et al. (2013), ERL 8:015031, Table 5 p. 8 (operations) | review |
| G4 | Towers, F-class, no capture (NETL case B31A, 727 MW net, ISO site at 15 °C) | 3.1 gpm/MW net = **186** | 4.0 gpm/MW net = **240**; process discharge 0.9 gpm/MW = 54 | NETL (2022), Cost and Performance Baseline Vol. 1 Rev. 4a, DOE/NETL-2023/4320, Exhibit ES-4 p. 9; site conditions Exhibit 2-2 p. 34; 4 cycles of concentration, p. 35 | model |
| G5 | Towers, H-class, no capture (NETL case B32A, 992 MW net) | 2.8 gpm/MW = **168** | 3.6 gpm/MW = **216** | same, Exhibit ES-4 p. 9 | model |
| G6 | Towers (U.S. fleet, heat-budget model) | 2010: 0.20 gal/kWh = 200; 2015: 0.18 = 180 | 2010: 0.29 = 290; 2015: 0.25 = 250 | Diehl and Harris (2014), USGS SIR 2014-5184, Tables 8-9 p. 15; Harris and Diehl (2019), USGS SIR 2019-5103, Tables 6-7 p. 11 | model |
| G7 | Towers (U.S. fleet, EIA-reported) | 2010: 280 | 2010: 540 | Diehl and Harris (2014), Tables 8-9 p. 15, "EIA 2010" columns | reported |
| G8 | Dry (air-cooled condenser) | median 2 (0-4), n = 2 | median 2 (0-4) | Macknick et al. (2012), Tables 2-3 | review |
| G9 | Dry | median 4 (4-120), n = 4 | median 4 (1-4) | Meldrum et al. (2013), Table 5 p. 8 | review |
| G10 | Hybrid (parallel wet and dry; "HYB-C", dry element carries 30% of the design heat load) | about half of all-wet: the hybrid uses on average 314,000 kgal/yr more than all-dry against 592,700 for all-wet (53%) | not given separately | Maulbetsch and DiFilippo (2018), CEC-500-2018-015, p. 5 (design), p. 68 (water); 530 MW plants at five California sites | model |
| G11 | Once-through | median 100 (20-100), n = 3 | median 11,380 (7,500-20,000), n = 2 | Macknick et al. (2012), Tables 2-3 | review |
| G12 | Once-through | median 100 (20-230), n = 8 | median 9,000 (7,200-21,000), n = 7 | Meldrum et al. (2013), Table 5 p. 8 | review |
| G13 | Once-through, fresh (fleet) | model 2010: 0.12 gal/kWh = 120 (forced evaporation); 2015: 0.15 = 150 | model 2010: 11 gal/kWh = 11,000; 2015: 14 = 14,000. EIA-reported 2010: 26,000 | Diehl and Harris (2014), Tables 8-9 p. 15; Harris and Diehl (2019), Tables 6-7 p. 11 | model, reported |
| G14 | Pond | 240 (n = 1) | 5,950 (n = 1) | Macknick et al. (2012), Tables 2-3 | review |

### 1b. Simple cycle, engines, fuel cells

| # | Technology | Consumption, gal/MWh | Withdrawal, gal/MWh | Source | Status |
|---|---|---|---|---|---|
| S1 | Combustion turbine (simple cycle), all water uses | median 50 (50-340), n = 3 | 430, n = 1 | Meldrum et al. (2013), Table 5 p. 8 | review |
| S2 | Combustion turbine with water or steam injection for NOx | **24-56** at a water-to-fuel mass ratio of 0.5-1.0 | add demineralization reject: about 1.3 × consumption at 75% recovery [A] | Derived. AP-42 §3.1.4.1 (4/00), p. 3.1-6: water or steam "typically injected at a water-to-fuel weight ratio of less than one", with a 2-3% efficiency penalty and 5-6% more output. Heat rates 9,124 (aeroderivative) and 9,905 Btu/kWh (frame), EIA AEO2023 Table 1; to 10,500 [A]. Gas at 22,480 Btu/lb HHV (NETL Rev. 4a, B31A fuel input over fuel flow, Exhibit ES-4 p. 9) | derived [A] |
| S3 | Combustion turbine with dry low-NOx combustion | 0 for NOx control | 0 | AP-42 §3.1 p. 3.1-3 (newer turbines use lean premixed combustion) and §3.1.4.2 p. 3.1-6 | review |
| S4 | Combustion turbine inlet evaporative cooling or fogging, in the hours it runs | **about 7-16** per MWh while running (West Michigan design day 31 °C / 22.5 °C wet-bulb: 7; central Texas 37 / 23 °C: 11; hot and dry 40 / 20 °C: 16) | about the same, plus any blowdown of the media [A] | Derived: air flow 8,040 kg/h per MW of turbine output (NETL B31A, stream 1, 3,834,126 kg/h for 477 MW of turbine output, Exhibit 5-9 p. 564 and stream table), cooled at 90% effectiveness toward the wet-bulb [A], water = air flow × rise in humidity ratio. Restores 15-20% of output when it cools the inlet 40-50 °F (EPA CHP Catalog, 2017, p. 3-11) | derived [A] |
| S5 | Reciprocating engines (radiator cooling) | about 0 | about 0 | EPA CHP Catalog (2017), p. 1-13: engines, turbines, microturbines and fuel cells "use almost negligible amounts of water"; jacket heat goes to "a cooling tower or a radiator when there is excess heat", p. 2-8 | review |
| S6 | Fuel cells | 0 in normal operation; water at start-up not quantified | 0 | EPA CHP Catalog (2017), p. 6-16 (a phosphoric acid system condenses its product water and is "water self-sufficient"); one manufacturer's solid oxide datasheets list water as "None during normal operation" (Bloom Energy Server datasheets 2024-2026; vendor claim, not independently measured; volume at start-up not stated, UNVERIFIED) | review |

Heat rates used above (Btu/kWh, EIA's higher heating value convention [A: the AEO table's footnote read here does not
state the basis]): combined cycle 6,370-6,431, aeroderivative turbine 9,124, frame turbine 9,905, engines 8,295, fuel
cells 6,469 (EIA AEO2023, Table 1, p. 2). Smaller units run higher: turbines of 3-44 MW at 9,488-14,247 HHV (EPA CHP
Catalog, Table 3-2 p. 3-6); engines of 0.1-9.3 MW at 8,207-12,637 HHV (Table 2-2 p. 2-10); fuel cells of 0.7-1,400 kW
at 6,272-9,948 HHV (Table 6-3 p. 6-13).

### 1c. Solar PV and wind, operations

| # | Technology | Consumption, gal/MWh | Withdrawal | Source | Status |
|---|---|---|---|---|---|
| R1 | Utility PV | median 1 (0-5), n = 3; "most PV system operators do not wash panels" (p. 3) | = consumption | Macknick et al. (2012), Table 1 p. 5 | review |
| R2 | Utility PV | median 26 (0-33), n = 3 | = consumption | Macknick et al. (2011), Table 1 p. 12 (superseded by R1; kept because it is the TP number often cited) | review |
| R3 | Flat-panel PV | median 6 (1-26), n = 9 | = consumption | Meldrum et al. (2013), Table 11 p. 12 | review |
| R4 | PV, desert Southwest (module washing plus staff) | 0.050-0.051 AF/MW/yr washing + 0.001-0.005 potable = **0.051-0.053 AF/MW/yr**; about **9 gal/MWh** at a 20% capacity factor | = consumption | Klise et al. (2013), SAND2013-5238, Table 1 p. 16 (from the BLM Solar PEIS method); 9 gal/MWh, p. 30 | model |
| R5 | Onshore wind | median 0 (0-0); TP: 0 (0-1) | = consumption | Macknick et al. (2012), Table 1 p. 5; (2011) Table 1 p. 12 | review |
| R6 | Onshore wind | median < 1 (0.1-2), n = 10 | median 1 (1-1) | Meldrum et al. (2013), Table 12 p. 13 | review |

### 1d. Construction and manufacturing (one-time)

| # | Technology | Figure | Source | Status |
|---|---|---|---|---|
| K1 | PV, construction at the site (desert Southwest) | peak construction year **1.3-5.7 AF/MW** (0.43-1.86 million gal/MW), almost all dust control; later years 30% of peak | Klise et al. (2013), Table 1 p. 16 and p. 15 | model |
| K2 | PV, annualized | construction 298 gal/MWh against 9 for O&M, for one hypothetical 600 GWh/yr facility at a 20% capacity factor (the basis of "annual" is not explained) | Klise et al. (2013), p. 30 | model |
| K3 | Crystalline-silicon PV, life cycle outside operations (manufacturing, construction, decommissioning) | consumption median 81 (10-210) gal/MWh; withdrawal 94 (1-1,600) | Meldrum et al. (2013), Table 11 p. 12 | review |
| K4 | Wind, life cycle outside operations | consumption median 1 (0.1-9) gal/MWh; withdrawal 26 (13-83) | Meldrum et al. (2013), Table 12 p. 13 | review |
| K5 | Wind, foundation concrete | 320-505 cubic yards (245-386 m³) of concrete per turbine (UNVERIFIED: search results for a South Dakota PUC permit appendix and a developer's page). At 0.15-0.18 m³ of mix water per m³ [A], **about 10,000-18,000 gal per turbine** before curing and road dust control [A] | derived [A] |
| K6 | Gas combined cycle, life cycle outside operations (mostly dust control in construction) | about 1 gal/MWh | Meldrum et al. (2013), Table 5 p. 8 | review |

Upstream fuel water is outside the packages' boundary (campus plus grid-level power plant water) and is listed only for
scale: conventional gas 4 (1-26) gal/MWh consumed, shale gas 16 (3-210) (Meldrum et al. 2013, Table 5 p. 8).

### 1e. Aggregates of plant reports, for scale

| # | Figure | Source | Status |
|---|---|---|---|
| A1 | U.S. combined cycle fleet, 2021: **2,803 gal/MWh withdrawn** (all cooling types; once-through plants dominate the average) | EIA, Today in Energy, June 14, 2023, "U.S. electric power sector continues water efficiency gains" | reported |
| A2 | All gas generation by balancing authority, 2024, generation-weighted (EIA-930 "gas" class: combined cycle, turbines, engines and gas steam together): U.S. 175 consumed / 4,205 withdrawn; MISO 191 / 6,527; ERCOT 196 / 2,792; PJM 124 / 1,174 gal/MWh. Monthly MISO consumption runs 150 (February) to 223 (May) | the package's `ba_fuel_water_2024.csv` (EIA-923 Schedule 8D and EIA-860, summed by BA and fuel; design 0008), my generation weighting | reported, aggregate |

The aggregates mix technologies and cooling types and are not a factor for a new plant. They show that a new tower-cooled
combined cycle (G1-G6) consumes about what the average gas MWh does, and withdraws a small fraction of it.

## 2. Ranges by technology (working values)

| Technology and cooling | Consumed, gal/MWh | Withdrawn, gal/MWh | Basis |
|---|---|---|---|
| Combined cycle, towers | 170-210 central, 130-300 range | 215-255 central, 150-290 range (to 760 in Meldrum) | G1-G6; G4's 186 / 240 at ISO conditions closes the energy balance (§4) |
| Combined cycle, hybrid | about 40-60% of towers for a design like HYB-C; anywhere from dry to wet depending on the dry share | same share | G10; physical, set by hours in wet mode |
| Combined cycle, dry | 0-4 (to 120 in one estimate) | 0-4 | G8, G9 |
| Combined cycle, once-through | 20-230 (forced evaporation at the water body) | 7,200-21,000 | G11-G13 |
| Simple-cycle turbine, dry low-NOx, no inlet cooling | about 0 | about 0 | S3 |
| Simple-cycle turbine with water injection | 24-56 | 30-75 [A] | S2 |
| Inlet evaporative cooling, hours in use | +7-16 | +7-16 | S4 |
| Reciprocating engines, radiators | about 0 | about 0 | S5 |
| Fuel cells | about 0 | about 0 | S6 |
| Solar PV, operations | 0-5 in humid climates [A: rain cleans; R1 notes most operators do not wash]; 6-26 where washed | = consumed | R1, R3, R4 |
| Wind, operations | 0-2 | 0-1 | R5, R6 |
| PV construction, one-time | up to 0.4-1.9 million gal per MW in the desert Southwest; less where dust control is lighter [A] | = consumed | K1 |
| Wind construction, one-time | about 10,000-18,000 gal per turbine of mix water, plus curing and roads [A] | = consumed | K5 |

What drives the spread:

1. **Cooling type, not fuel.** Macknick et al. (2012) conclude that factors agree better when grouped by cooling than by
   fuel. For a new plant the choice among towers, hybrid, dry and once-through moves withdrawal by four orders of
   magnitude and consumption by two.
2. **Cycles of concentration** set tower withdrawal: many plants run 2-4 cycles, 5-8 are possible, and withdrawal is
   typically 115-150% of consumption for freshwater towers (Diehl and Harris 2014, p. 12). USGS computes tower withdrawal
   as 1.4 × consumption at 3.5 cycles (p. 13). NETL assumes 4 (Rev. 4a, p. 35).
3. **The steam share.** In a combined cycle only the steam turbine rejects heat to a condenser: in B31A, 263 of 740 MW
   gross is steam (Exhibit 5-9 p. 564). A simple-cycle turbine has no condenser, which is why its water is only
   injection and inlet cooling.
4. **Weather**, through the tower's evaporative share and through heat rate (§3).

## 3. Heat rate, output and ambient temperature, hour by hour

| Technology | Output | Efficiency or heat rate | Source |
|---|---|---|---|
| Combustion turbine (7.5 MW reference unit) | 80% of ISO output at 100 °F, 107% at 40 °F (ISO = 59 °F, sea level): about −0.9%/K above 15 °C | efficiency −8% at 100 °F, +2% at 40 °F: heat rate about +0.35%/K | EPA CHP Catalog (2017), §3.4.4.1 p. 3-10 and Fig. 3-5 |
| Combustion turbines (planning study) | −1.0% of capacity per °C above 15 °C (assumed) | — | Sathaye et al. (2011), LBNL, p. 11 |
| Combined cycle, wet cooling | −0.3 to −0.5% of capacity per °C above 15 °C | — | Sathaye et al. (2011), p. 11, citing Maulbetsch and DiFilippo (2006) |
| Combined cycle, dry cooling | about −0.7% of capacity per °C | — | same |
| Combined cycle, dry vs wet on the hot day | dry loses more than 20 MW of a 530 MW plant at the 1% dry-bulb (about 4%); HYB-C 4 MW | annual output −60,700 MWh, dry against wet | Maulbetsch and DiFilippo (2018), p. 68 |
| Combined cycle, dry vs wet over a year | — | annual performance penalty 1.7% | Macknick et al. (2011), p. 15, citing EPA's §316(b) analysis |
| Combined cycle, towers, measured (hours above the 90th temperature percentile) | — | median −0.06 percentage points of efficiency per °C (−0.29 to +0.16) across U.S. units; theoretical models give larger losses | Meng and Sanders (2019), Applied Energy 253:113486, §4. Read as percentage points [A], since it is compared with one plant's 50.95% to 48.01% over 15-45 °C (−0.098 points per °C) |
| Reciprocating engines | about −1% for every 10 °F above 77 °F (−0.18%/K above 25 °C) | same | EPA CHP Catalog (2017), §2.4.2 p. 2-12 |
| Fuel cells | small; from blowers and compressors | small | EPA CHP Catalog (2017), §6.4.3 p. 6-15 |
| Water or steam injection | +5-6% output | −2-3% efficiency | AP-42 §3.1.4.1, p. 3.1-6 |

What it means hour by hour:

- **Capacity is lowest when a data center needs the most.** A turbine plant sized at ISO conditions has about 80% of its
  rating on a 38 °C afternoon. On-site generation sized to carry the campus therefore has to be sized at the site's
  design dry-bulb, not at ISO, or it leaves hours unserved; this is one reason the overbuild in §6 is large.
- **More fuel per MWh on hot hours.** Heat rate rises a few tenths of a percent per kelvin for turbines and less for
  combined cycle, so fuel and the heat to be rejected per MWh both rise. For a combined cycle on towers, the water per
  MWh then follows from that heat and the hour's weather through the same tower physics the packages already use.
- **Dry cooling costs output, not water.** The penalty falls on the hottest hours; the CEC study puts it near 4% of a
  plant's rating on the hot day.
- **Inlet cooling trades water for output** in the hours it runs: about 7-16 gal per MWh (S4) for 15-20% more output.
- **Part load raises heat rate.** A lean-burn gas engine's efficiency at half load is about 8-10% below full load;
  gas turbines typically lose 15-25% at half load, which is why "multiple engines may be preferable to a single" large
  unit (EPA CHP Catalog, §2.4.1 p. 2-11). A plant following a data center's load runs part of its units at part load
  every hour; how it commits units is a dispatch rule [A].

## 4. Energy balance check for a tower-cooled combined cycle

NETL's B31A rejects 1,406 GJ/h (1,332 MMBtu/h) in its condenser for 727 MW net (Exhibit 5-9 p. 564): 0.537 MW of
heat per MW of net output. If all of it left by evaporation at 2.45 MJ/kg, the tower would evaporate 208 gal/MWh. NETL's
consumption is 186 gal/MWh (89% of that), and the difference is about what the sensible share of tower heat transfer
explains (the packages' evaporative ratio, after Rutberg et al. 2011, gives 75-90% across ordinary weather). Blowdown at
4 cycles adds a third of evaporation, about 60 gal/MWh, giving a withdrawal near NETL's 240. So a gas plant built on the
packages' `heat_rejection` with its condenser heat as the load should land on the published factors without tuning.
This is my arithmetic and an estimate; the test belongs in the model's checks.

The same balance gives the plant's fuel role: fuel in = net output + condenser heat + stack and other losses. For B31A,
HHV input 1,355 MW (Exhibit ES-4 p. 9) = 727 net + 391 condenser + 237 other (stack, auxiliaries, generator losses).

## 5. Hourly solar and wind from weather the packages already use

**Data.** The packages read ERA5 from Open-Meteo's open copy on AWS (`s3://openmeteo/data/copernicus_era5`; design
0004). Its listing (checked Nov 10, 2026) carries `shortwave_radiation`, `direct_radiation`, `wind_u_component_100m` and
`wind_v_component_100m` beside the `temperature_2m` and `dew_point_2m` the packages fetch now. Open-Meteo documents
radiation as the mean over the preceding hour and wind as instantaneous (Historical Weather API page). So hourly PV and
wind can come from the same cells and the same 30 years as the user's water and the grid's factors, and a heat wave
meets the campus's load, the turbines' derate and the panels' output in the same hours.

**PV, by the PVWatts method** (Dobos 2014, NREL/TP-6A20-62641), the method pvlib implements (Holmgren et al. 2018):

1. Sun position for each hour, evaluated at the middle of the hour because ERA5 radiation is a preceding-hour mean.
2. Beam and diffuse on the horizontal: ERA5 gives both (`direct_radiation`, and diffuse = shortwave − direct), so no
   decomposition model is needed. Direct normal = direct / cos(zenith), clipped near the horizon [A].
3. Plane of array for single-axis trackers (99% of new U.S. projects in 2024; LBNL Utility-Scale Solar 2025 data
   update, slide 5) or fixed tilt, with a sky diffuse model (isotropic or Hay-Davies) and ground reflection.
4. Cell temperature from air temperature, irradiance and wind (PVWatts' or Faiman's model); DC power with a temperature
   coefficient near −0.37%/K for crystalline modules [A: PVWatts' standard module]; inverter efficiency and clipping at
   an inverter loading ratio of 1.2-1.4 [A]; system losses about 14% (PVWatts default) [A].

**Wind:** ERA5 100 m wind speed from the u and v components, adjusted to hub height with a power law (exponent near 1/7)
[A], through a published reference turbine power curve (for example the IEA 3.4 MW onshore reference turbine;
Bortolotti et al. 2019, NREL/TP-5000-73492, UNVERIFIED in this session), with plant losses for wakes, availability and
electrical losses of about 10-20% [A]. Davidson and Millstein (2022, Wind Energy 25(9):1646-1653) tested ERA5 against
seven years of hourly output from more than 100 Texas wind plants: errors were small averaged by day and larger by hour,
and accuracy fell through the evening; a Berkeley Lab summary gives ERA5 within ±20% of recorded capacity factor in 78% of
hours and 99% of days (the summary figures are UNVERIFIED against the paper). Staffell and Pfenninger (2016, Energy
114:1224-1239) and Pfenninger and Staffell (2016, Energy 114:1251-1265) show the bias correction reanalysis wind and PV
need against measured output; whether ERA5 needs it at the packages' cells is a check to run (0014).

**Capacity factors to check against:**

| Figure | Value | Source |
|---|---|---|
| U.S. wind, annual | 35.9% (2022), 33.2% (2023), 34.3% (2024), 33.8% (2025) | EIA Electric Power Monthly, Table 6.07.B |
| U.S. utility PV, annual (AC) | 24.4% (2022), 23.2% (2023), 23.2% (2024), 24.0% (2025) | same |
| U.S. wind, 2024 | 34% fleet-wide (projects built 1998-2023); 37.5% for projects built in 2023 | LBNL, Land-Based Wind Energy Technology Update 2025, figure file slide 43 |
| U.S. utility PV by region | cumulative net AC capacity factor about 25% (7-37% by project); regional averages 17% (least sunny) to 31%; tracking adds about 5 points | LBNL, Utility-Scale Solar 2025 data update, slides 5, 38, 39 |
| State wind, 2023-2024 | Michigan 27-31%, Indiana 29-34%, Ohio 29%, Wisconsin 24-28%, Texas 34-35% | Estimate: EIA state generation (API, electric-power-operational-data) over EIA-860M nameplate at December 2023 [A: capacity added during the year biases these] |
| State utility PV, 2023-2024 | Michigan about 15-22%, Texas about 21-31% (bracketed: 2023 generation over end-2023 capacity reads low, 2024 over end-2023 capacity reads high, because capacity grew fast) | same method, estimate [A] |

The state solar brackets are too wide to use as a check; the regional values in LBNL's interactive data
(emp.lbl.gov/pv-capacity-factors) are the better target. The hourly check that fits the scope rule is EIA-930's hourly
solar and wind generation for a balancing authority, normalized by the BA's capacity: aggregate, no plant named.

## 6. On-site generation at data centers: how it is sized

From public studies and standards, in general terms:

- **Redundancy.** Uptime Institute's Tier III is concurrently maintainable at N+1, for every component and path, and Tier
  III and IV engine-generator capacity is based on the manufacturer's unlimited-runtime rating at site conditions
  (Traver, Uptime Institute, IEA EBC Annex 75 presentation, Oct 2020; the Tier Standard itself was not read,
  UNVERIFIED). Designs at 2N appear in industry practice (a trade magazine article, csemag.com, secondary). For prime power
  the same logic gives N+1 or N+2 units sized at the hottest design hour.
- **Ratings.** Engines are rated standby (under about 100 hours), prime (unlimited hours with varying load, 80-85% of
  standby) and baseload (70-75% of standby) (EPA CHP Catalog, p. 2-10). A unit carrying a campus around the clock runs
  at its baseload rating, not its standby rating.
- **Overbuild.** The IEA estimates 15-27 GW of on-site gas could power data centers by 2030, mostly in the United States,
  and that reliable on-site gas supply "requires overbuilding onsite generation infrastructure by 30% to 70% relative to
  demand" (IEA, Key Questions on Energy and AI, 2026, executive summary). The same summary notes AI load swings of more
  than 50% of rated capacity within a second, which on-site plants must follow.
- **Arithmetic of the overbuild** [A]: a 300 MW peak campus on 20 MW units needs 15 units; N+2 is 17 (13% over); sized
  at a 35 °C design hour with a 10% turbine derate, 19 (27% over); at the baseload rating of a standby-rated engine
  (70-75%), more again. The IEA range is about what redundancy, hot-hour derate and rating together give.
- **Islanded or grid-parallel.** An islanded campus carries all of its load on its own plant and leaves hours unserved
  only if the plant falls short; a grid-parallel campus runs its plant against a grid connection that takes the rest
  or serves as backup. Studies of flexible large loads (Norris et al. 2025, Duke Nicholas Institute, "Rethinking Load
  Growth") estimate nearly 100 GW of new load could be served across U.S. balancing authorities if it accepts brief,
  modest curtailment (their per-rate figures, 76, 98 and 126 GW at 0.25, 0.5 and 1% curtailment, are UNVERIFIED in
  this session); curtailed hours are exactly where an on-site plant or a battery would serve.
- **Technologies in public statements**, without naming projects: aeroderivative and frame turbines (simple and combined
  cycle), reciprocating engines in blocks, and solid oxide fuel cells. Turbines are in short supply (IEA 2026).
- **Renewable PPAs.** Buyers match on an annual basis (annual MWh of renewables equal to annual load) or hourly
  ("24/7"), and the two give very different hourly residuals and system effects (Riepin and Brown 2024, Energy
  Strategy Reviews 54:101488; Xu et al. 2024, Joule, "System-level impacts of voluntary carbon-free electricity
  procurement strategies", authors UNVERIFIED in this session). A virtual (financial) PPA does not change which plants
  physically run in a given hour; a physical or co-located one does.

## 7. Gaps and assumptions

1. **No measured water for a new gas plant serving one load.** Every per-MWh figure is a fleet average, a design study
   or a review. The check against EIA-923 can only be by technology, cooling type and region, in aggregate [A].
2. **Simple-cycle water** rests on Meldrum's three estimates and my arithmetic from AP-42's water-to-fuel ratio. Whether
   a given turbine class uses water injection or dry low-NOx is a scenario setting [A]; the share of new units on each
   is not sourced.
3. **Inlet cooling** water (S4) is derived from one air flow per MW (NETL's F-class) and an assumed 90% effectiveness
   [A]; aeroderivative units differ.
4. **Hybrid cooling** has one design study (California sites). Its water share is set by the dry element's size and
   the hours above the switch point; the packages' hybrid physics already models that [A].
5. **Part-load heat rate**: only the half-load points above (engines −8-10%, turbines −15-25%, EPA CHP Catalog p. 2-11);
   the curve between them and for combined cycle is [A].
6. **Combined cycle heat rate against temperature**: measured fleet responses (Meng and Sanders 2019) are an order of
   magnitude smaller than theoretical ones; the interpretation as percentage points is mine [A].
7. **PV washing in the Great Lakes and Texas**: no regional figure; the Southwest BLM method (R4) is an upper bound [A].
8. **Construction water**: PV figures are for the desert Southwest; wind foundations rest on unverified concrete volumes
   and an assumed mix water ratio [A]. Both are one-time totals, reported separately from annual water.
9. **ERA5 bias for wind and solar at the packages' cells** is not yet measured. The Texas evaluation (Davidson and
   Millstein 2022) is the closest; Great Lakes cells are not covered [A].
10. **Reference turbine and PV system parameters** (hub height, power curve, losses, inverter loading, temperature
    coefficient) are set, not sourced from projects [A].
11. **Upstream fuel water** (gas production) is outside the boundary and not added [A: the boundary decision].
12. **Uptime Tier Standard, Duke per-rate figures, the IEA reference turbine report and the Joule authors** were not
    read in full in this session (UNVERIFIED).
13. **Once-through gas plants** on a Great Lake would fall under the §316(b) new-facility rule (40 CFR 125.84), which
    holds intake near closed-cycle levels; the number stays true to the physics and the rule is a flagged note, as for
    other users (`once_through`).

## Sources

Primary documents read in this session:

- Macknick, J., Newmark, R., Heath, G., and Hallett, K. C. (2012). Operational water consumption and withdrawal factors
  for electricity generating technologies: a review of existing literature. Environ. Res. Lett. 7:045802.
  doi:10.1088/1748-9326/7/4/045802. https://openei.org/datasets/files/969/pub/1748-9326_7_4_045802.pdf
- Macknick, J., Newmark, R., Heath, G., and Hallett, K. C. (2011). A Review of Operational Water Consumption and
  Withdrawal Factors for Electricity Generating Technologies. NREL/TP-6A20-50900. https://www.osti.gov/servlets/purl/1219149
- Meldrum, J., Nettles-Anderson, S., Heath, G., and Macknick, J. (2013). Life cycle water use for electricity
  generation: a review and harmonization of literature estimates. Environ. Res. Lett. 8:015031.
  doi:10.1088/1748-9326/8/1/015031
- NETL (2022). Cost and Performance Baseline for Fossil Energy Plants, Volume 1: Bituminous Coal and Natural Gas to
  Electricity, Revision 4a. DOE/NETL-2023/4320, Oct 14, 2022. https://www.osti.gov/biblio/1893822
- Diehl, T. H., and Harris, M. A. (2014). Withdrawal and consumption of water by thermoelectric power plants in the
  United States, 2010. USGS SIR 2014-5184. https://pubs.usgs.gov/sir/2014/5184/
- Harris, M. A., and Diehl, T. H. (2019). Withdrawal and consumption of water by thermoelectric power plants in the
  United States, 2015. USGS SIR 2019-5103. https://pubs.usgs.gov/sir/2019/5103/sir20195103.pdf
- Maulbetsch, J. S., and DiFilippo, M. N. (2018). Evaluating Cost, Performance and Water Conserving Capability of Hybrid
  Cooling. California Energy Commission, CEC-500-2018-015.
  https://www.energy.ca.gov/sites/default/files/2021-06/CEC-500-2018-015.pdf
- U.S. EPA (2017). Catalog of CHP Technologies (full document, Sept 2017 revision).
  https://www.epa.gov/sites/default/files/2015-07/documents/catalog_of_chp_technologies.pdf
- U.S. EPA (2000). AP-42, Fifth Edition, Volume I, Section 3.1, Stationary Gas Turbines (4/00).
  https://www.epa.gov/sites/default/files/2020-10/documents/c03s01.pdf
- U.S. EIA (2023). Cost and Performance Characteristics of New Generating Technologies, Annual Energy Outlook 2023,
  Table 1. https://www.eia.gov/outlooks/aeo/assumptions/pdf/elec_cost_perf.pdf
- Sathaye, J., Dale, L., Fitts, G., Larsen, P., Koy, K., Lewis, S., and Lucena, A. (2011). Estimating Risk to
  California Energy Infrastructure from Projected Climate Change. LBNL for the California Energy Commission.
  https://www.osti.gov/servlets/purl/1026811
- Meng, M., and Sanders, K. T. (2019). A data-driven approach to investigate the impact of air temperature on the
  efficiencies of coal and natural gas generators. Applied Energy 253:113486. https://par.nsf.gov/servlets/purl/10120498
- Klise, G. T., Tidwell, V. C., Reno, M. D., Moreland, B. D., Zemlick, K. M., and Macknick, J. (2013). Water Use and
  Supply Concerns for Utility-Scale Solar Projects in the Southwestern United States. SAND2013-5238.
  https://www.osti.gov/servlets/purl/1090206
- LBNL (2025). Utility-Scale Solar, 2025 Data Update (slides).
  https://emp.lbl.gov/sites/default/files/2025-10/Utility%20Scale%20Solar%202025%20Edition%20Slides.pdf
- LBNL (2025). Land-Based Wind Energy Technology Update, 2025 Edition (figure file).
  https://emp.lbl.gov/sites/default/files/2025-08/FIGURE%20FILE_Land-Based%20Wind%20Energy%20Technology%20Update_2025%20Edition.pdf
- U.S. EIA, Electric Power Monthly, Table 6.07.B, capacity factors for non-fossil generators.
  https://www.eia.gov/electricity/monthly/epm_table_grapher.php?t=epmt_6_07_b
- U.S. EIA (2023). U.S. electric power sector continues water efficiency gains. Today in Energy, June 14, 2023.
  https://www.eia.gov/todayinenergy/detail.php?id=56820
- U.S. EIA API v2: electricity/electric-power-operational-data (state generation by fuel) and
  electricity/operating-generator-capacity (EIA-860M), queried Nov 10, 2026.
- Open-Meteo, Historical Weather API documentation (variables, averaging): https://open-meteo.com/en/docs/historical-weather-api;
  open-data ERA5 listing: https://openmeteo.s3.amazonaws.com/?list-type=2&prefix=data/copernicus_era5/&delimiter=/
- IEA (2026). Key Questions on Energy and AI, executive summary.
  https://www.iea.org/reports/key-questions-on-energy-and-ai/executive-summary

Cited from abstracts, summaries or secondary sources (figures marked UNVERIFIED where used):

- Dobos, A. P. (2014). PVWatts Version 5 Manual. NREL/TP-6A20-62641.
- Holmgren, W. F., Hansen, C. W., and Mikofski, M. A. (2018). pvlib python: a python package for modeling solar energy
  systems. Journal of Open Source Software 3(29):884. doi:10.21105/joss.00884
- Davidson, M. R., and Millstein, D. (2022). Limitations of reanalysis data for wind power applications. Wind Energy
  25(9):1646-1653. doi:10.1002/we.2759
- Staffell, I., and Pfenninger, S. (2016). Using bias-corrected reanalysis to simulate current and future wind power
  output. Energy 114:1224-1239. Pfenninger, S., and Staffell, I. (2016). Long-term patterns of European PV output using
  30 years of validated hourly reanalysis and satellite data. Energy 114:1251-1265.
- Bortolotti, P., et al. (2019). IEA Wind TCP Task 37, WP2.1 Reference Wind
  Turbines. NREL/TP-5000-73492 (not read).
- Traver, T. (2020). Uptime Institute presentation, IEA EBC Annex 75 meeting, Oct 2020:
  https://nex75.iea-ebc.org/Data/Sites/4/media/events/2020-10/presentations/1.4b--traver--uptime-institute.pdf
  (from search results).
- Norris, T. H., Profeta, T., Patino-Echeverri, D., and Cowie-Haskell, A. (2025). Rethinking Load Growth: Assessing the
  Potential for Integration of Large Flexible Loads in US Power Systems. Duke Nicholas Institute, Feb 2025 (full text
  not read: access blocked).
- Riepin, I., and Brown, T. (2024). On the means, costs, and system-level impacts of 24/7 carbon-free energy
  procurement. Energy Strategy Reviews 54:101488. doi:10.1016/j.esr.2024.101488
- Xu, Q., et al. (2024). System-level impacts of voluntary carbon-free electricity procurement strategies. Joule.
- Bloom Energy, Energy Server datasheets (2024, 2025, Feb 2026), water "None during normal operation":
  https://www.bloomenergy.com/wp-content/uploads/bloom-energy-server-datasheet-2025.pdf (from search results).
- Wind foundation concrete volumes (320-505 cubic yards): search results for a South Dakota PUC docket appendix
  (https://puc.sd.gov/commission/dockets/electric/2017/el17-055/appendixa.pdf) and a developer's page; not read.
