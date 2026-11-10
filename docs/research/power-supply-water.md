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

## 8. Where new gas plants' wastewater goes (design 0014, decision 10)

Added Nov 10, 2026. Decision 10 sets the gas plant's return by the place's default wastewater rule, "as long as it is
realistic". This section checks that against what new U.S. gas plants actually do with cooling tower blowdown,
demineralizer and RO reject and other process wastewater. Patterns only: no plant is named, and the counts below were
built from the federal forms by a script that writes only aggregates (kept outside the repository).

### 8a. What the rules cover

- **Combined cycle is under the steam electric guidelines; nothing else here is.** 40 CFR 423.10 applies to units using
  "a thermal cycle employing the steam water system", and since 2015 says outright that it covers "both the combustion
  turbine and steam turbine portions of a combined cycle generating unit" (eCFR, current text). EPA's 2015 technical
  development document sorts "stand-alone combustion turbines, internal combustion engines, fuel cells, and wind
  turbines" into the non-steam-electric group outside the category (EPA-821-R-15-007, p. 4-4). Their wastewater is
  permitted case by case (best professional judgment in an NPDES permit, or a sewer authority's local limits).
- **What a combined cycle discharges.** EPA lists "cooling water, boiler blowdown, metal cleaning wastes, and steam
  condensate water treatment wastes", with no ash or FGD water (same, §4.2.2, p. 4-7). Ion exchange regeneration,
  boiler blowdown, floor drains and tower basin cleaning are "low volume waste sources" (40 CFR 423.11(b)).
- **New-source limits on a direct discharge** (40 CFR 423.15(a)): low volume wastes TSS 100 mg/L daily maximum and 30
  monthly, oil and grease 20 and 15; cooling tower blowdown free available chlorine 0.5 maximum and 0.2 average, no
  detectable amount of the 126 priority pollutants from tower chemicals except chromium 0.2 and zinc 1.0 mg/L, and
  chlorine released from one unit at a time for no more than two hours a day. **To a sewer** (PSNS, 423.17(a)), the same
  priority-pollutant limits on blowdown apply, plus the POTW's own local limits.
- **Design studies assume conventional treatment is enough.** NETL's baseline finds "no additional control technology
  considerations are required for NGCC compliance with the ELG rule" (Rev. 4a, p. 41). It assumes makeup "50 percent by
  a publicly owned treatment works (POTW) and 50 percent from groundwater" and blowdown "treated and 90 percent returned
  to the water source" (pp. 51-52). In case B31A the process discharge is 657 of 2,902 gpm withdrawn (23%), of which
  651 gpm is tower blowdown and 5.6 gpm the deaerator vent; boiler feedwater makeup is 5.6 gpm, 0.5 gal/MWh net
  (Exhibit 5-14, p. 567). So in a tower-cooled combined cycle, blowdown is almost all of the wastewater, and the
  demineralizer reject is under 1% of it [derived: reject at 25-30% of a 5.6 gpm feed, A].

### 8b. Combined cycle plants since 2005, from EIA-860 and EIA-923 (aggregate)

**Method.** EIA-860 2024, Schedule 6 Part D (`6_2_EnviroEquip_Y2024.xlsx`, Cooling sheet) gives each cooling system's
type, in-service year, water source code (SW surface, GW ground, PD "plant discharge water (ex: wastewater treatment
plant discharge)", OT), water type (fresh, brackish, saline, reclaimed), and a free-text "Cooling Water Discharge".
The instructions ask for the discharge water's name "if the discharge body of water is different than the source of
the cooling water" (EIA-860 instructions, Schedule 6 Part D, lines 5-8, pp. 45-46), so a blank beside a named surface
source reads as the same water body. Part D covers plants with 100 MW or more of steam-electric nameplate (p. 45), so
plants of about 200 MW and up appear and simple-cycle, engine and fuel cell plants do not. I kept operating cooling
systems in service 2005 or later and linked to natural gas combined cycle generators (EIA-923 2024 cooling detail
file), then sorted each plant's discharge text into the classes below by hand-checked rules. Plant size is the plant's
combined cycle nameplate (EIA-860 3_1, prime movers CA, CT and CS on gas).

**The fleet.** 156 plants: 108 with wet towers (induced, forced or natural draft, four of them hybrid wet-dry), 37 with
dry cooling only, 11 with once-through or cooling ponds (one plant has two kinds). Plant size: median 740 MW, quartiles
590-1,150 MW; only 5 of the 108 tower plants are under 300 MW.

**Where tower plants send their cooling water discharge** (plants; a plant with systems in two classes is counted
under the first):

| Destination | Plants | Share of 108 | Share of the 85 with a stated destination | Notes |
|---|---|---|---|---|
| Direct discharge to the same water body as the intake | 42 | 39% | 49% | 28 name the same water, 14 leave the field blank beside a named surface source; almost all (41) take surface water |
| Municipal sewer (POTW) | 18 | 17% | 21% | 7 of them take reclaimed effluent from the same POTW and return blowdown to it; 6 take groundwater; 3 surface water |
| Direct discharge to a different water body | 14 | 13% | 16% | 7 take groundwater and discharge to a stream or river; 3 take a utility's water or reclaimed effluent and discharge to a stream; 4 take one surface water and discharge to another |
| No discharge: zero liquid discharge, evaporation or on-site ponds, deep injection | 11 | 10% | 13% | ZLD 5 (4 in the West), ponds 4, injection 2 |
| Not stated or unclear | 23 | 21% | — | 15 blank beside a groundwater, reclaimed or utility source; 8 with text that names no water body |

By region (states grouped as West: AZ CA CO ID MT NV NM OR UT WA WY; Texas; the rest), stated destinations among the
tower plants are: rest of the country (77 plants) same water 33, sewer 14, different water 11, no discharge 5,
unstated 14; West (21) same 4, sewer 3, different 2, no discharge 6, unstated 6; Texas (10) same 5, sewer 1,
different 1, unstated 3. By supply: of 49 surface-supplied plants with a stated destination, 41 (84%) discharge to the
same water; of 35 plants on groundwater, a utility or reclaimed effluent with a stated destination, 15 go to a sewer,
10 to a stream and 10 discharge nothing. No pattern by size appears between 300-700 MW and 700 MW and up (sewer 8 and
10, same water 14 and 14), and five plants under 300 MW are too few to read.

**Volumes, EIA-923 Schedule 8D, 2024** (annual withdrawal and discharge summed over months, same cooling systems):
85 tower plants report withdrawal. Of the 64 that also report a discharge, discharge is a median 19% of withdrawal
(quartiles 14-27%), close to NETL's 23% at 4 cycles. 21 report no discharge at all: 5 of the 9 that state ZLD, ponds
or injection, 9 of the 18 whose destination is unstated, 3 of 14 sewered plants (a sewer discharge may not be reported
as a cooling discharge [A]) and 4 of 32 same-water plants (likely reporting gaps [A]). So between 10% and about 20% of
new tower plants discharge nothing [A: the upper end counts the unstated plants that report zero].

**Dry-cooled combined cycle.** EIA records no cooling water discharge for the 37 dry plants, as expected. Their
wastewater is boiler blowdown, demineralizer reject, drains and sanitary, about 1 gal/MWh or less [derived from NETL's
0.5 gal/MWh of feedwater makeup, A]. Where it goes is not in the federal forms.

**Limits of this reading.** The discharge field is free text, and the forms describe the cooling system's discharge,
not every process stream. A plant's NPDES permit is the record; counting outfalls from ECHO by plant type and receiving
water is a further check (not done here; it would need the ECHO facility download matched to EIA plant codes, still
in aggregate).

### 8c. Simple-cycle turbines, engines and fuel cells

No aggregate record of where their wastewater goes was found. What is sourced:

- Their process water is small: NOx water injection at 24-56 gal/MWh with its demineralizer reject, and inlet
  evaporative cooling at 7-16 gal/MWh in the hours it runs (§1b, S2 and S4); dry low-NOx units without inlet cooling,
  radiator-cooled engines and fuel cells use almost none (S3, S5, S6).
- Trade literature describes the wastewater of small combustion turbine plants as going to a city sewer through an oil
  separator "depending on permit requirements and the availability of 'city sewer'", with demineralizer regeneration
  left to the supplier of portable exchange units (Moore and Rittof 2007, a trade article, not a survey).
- Permit fact sheets for simple-cycle plants in the arid West describe evaporation ponds for evaporative cooler
  blowdown and RO reject (one Nevada NPDES fact sheet, from search results; UNVERIFIED as a pattern).

### 8d. On-site generation at data centers

Public sources rarely say where a data center plant's water goes. A 2026 survey of proposed gas plants serving data
centers counts at least sixteen combined cycle plants (40,896 MW) among them, notes that the others "would not need
water to run their turbines" and that "some power plants also plan to use air cooling", and says some water "may need
to be treated before being released back into the environment", without saying where (Environmental Integrity Project,
"The Power Behind AI", July 2026, p. 17; its 2,800 gal/MWh is the fleet's average withdrawal, A1, dominated by
once-through plants, not a factor for a new tower plant). The technologies in public statements (§6) are mostly simple-
cycle turbines, engines and fuel cells, which use little process water (§8c). Nothing found gives a destination for a
campus plant's blowdown; a plant inside a campus would most simply share the campus's water and sewer connection [A].

### 8e. Recommended default, and the roles gap

| Technology and supply | Default return (proposed) | Alternatives as settings | Basis |
|---|---|---|---|
| Combined cycle, towers or hybrid, on a surface water | `to_source`: a direct discharge to the same water body | sewer; a different stream; ZLD | 41 of 49 surface-supplied plants with a stated destination (8b) |
| Combined cycle, towers or hybrid, on groundwater or a utility's water | the place's wastewater rule (`to_sewer` where it fits) | a direct discharge to a nearby stream (about two-thirds as common as the sewer); no discharge, by ZLD or ponds (as common as the stream, more so in the West) | 15 sewer, 10 stream, 10 none of 35 (8b) |
| Combined cycle, towers, arid West | as above, with ZLD more likely | — | 6 of 15 Western plants with a stated destination discharge nothing |
| Combined cycle, dry | `to_sewer` for process wastewater of about 1 gal/MWh or less | hauled or evaporated where there is no sewer | NETL Exhibit 5-14 [A for the destination] |
| Simple-cycle turbine with water injection or inlet cooling | `to_sewer` [A] | hauled or evaporation pond | 8c; no aggregate found |
| Simple-cycle turbine with dry low-NOx and no inlet cooling; engines on radiators; fuel cells | `to_sewer` of a near-zero flow (washing, drains, sanitary) [A] | — | S3, S5, S6 |

By size: the federal forms cover combined cycle plants of about 200 MW and up and show no difference between the
300-700 MW and larger groups. Below that, and for every simple-cycle, engine and fuel cell plant, the default rests on
the technology's small flows and is [A].

**Is a discharge to a different water body common?** Yes, often enough to matter: 14 of 108 new tower plants (13%), and
16% of those whose destination is stated. Most of them take groundwater or a utility's water and discharge blowdown to
a local stream under their own NPDES permit, which is also NETL's design-study convention (half the makeup from a POTW,
half from groundwater, blowdown "returned to the water source"). That case is neither `to_sewer` (no POTW in between)
nor `to_source` (the receiving water is not the one drawn from). It is not special to gas plants: a data center or a
cell plant on wells with its own stream discharge is the same case. Settling it is a roles question for every type
(design 0010), for Andrew.

## 9. Renewables' land, runoff and construction (design 0014, decision 2's note)

Added Nov 10, 2026. Values for a hypothetical PV or wind project at the user's place, in the terms the shared runoff
code takes: `runoff.runoff_in(rain_in, imp, cover)` and `runoff.loads(acres, rain_in, before, imp)` (Simple Method,
an impervious share and a pervious cover's Rv), `runoff.storm_mg(acres, storm_in, imp)` and
`hydrology.composite_runoff_in(p_in, impervious, cn_pervious)` (TR-55 curve numbers for the impervious and pervious
parts, area-weighted), and `runoff.construction(acres_disturbed)` (tons of sediment a year of construction). No project
is named; where a source is one project's document it is cited as an anonymized example.

### 9a. Land per MW

| # | Technology | Figure | Source | Status |
|---|---|---|---|---|
| L1 | PV, fixed tilt, >20 MW (2012 and earlier) | direct area 5.8 acres/MWac (7 projects), total area 7.5 (14 projects), capacity-weighted | Ong et al. (2013), NREL/TP-6A20-56290, Tables 3-4 p. 10 | reported, review |
| L2 | PV, single-axis tracking, >20 MW | direct 9.0 acres/MWac (7 projects), total 8.3 (16); under 20 MW: direct 6.3, total 8.7 | same | reported, review |
| L3 | All solar, total and direct | total 8.9 acres/MWac capacity-weighted, direct 7.3 (direct counts arrays, access roads, substations and buildings) | Ong et al. (2013), p. v | review |
| L4 | PV built 2019, array area | median **2.8 acres/MWdc fixed tilt, 4.2 tracking** (power density 0.35 and 0.24 MWdc/acre); up 52% and 43% since 2011 | Bolinger and Bolinger (2022), IEEE J. Photovoltaics 12(2), summary slides p. 13; 736 plants of 5 MWac and up built 2007-2019 | reported (imagery) |
| L5 | Array share of the site | polygons cover arrays and nearby inverter pads, "NOT ... the total leased or owned area"; one example in the slides has the array on 69% of the leased area | same, slide 7 | example |
| L6 | PV, Western Interconnection, whole footprint with roads, fencing and buffers | mean 24.7 W per m² (about 10 acres/MW; AC or DC basis not stated in the summary) | Communications Earth & Environment (2025), 719 facilities, via a trade summary (pv magazine USA, Dec 15, 2025); UNVERIFIED | reported (imagery) |
| L7 | Onshore wind, total project area | **34.5 ± 22.4 ha/MW (85 acres/MW)**, 161 projects, 25,438 MW; capacity density 3.0 ± 1.7 MW/km² | Denholm et al. (2009), NREL/TP-6A2-45834, Table 1 p. 10, p. 14 | reported |
| L8 | Onshore wind, direct impact | **permanent 0.3 ± 0.3 ha/MW (0.7 acres/MW)**, 93 projects; **temporary 0.7 ± 0.6 ha/MW (1.7 acres/MW)**, 52 projects; together about 1.0 ± 0.7 ha/MW | same, Table 1 p. 10 and p. 12 | reported |
| L9 | Wind, what the permanent area is | roads 79%, turbine pads 10%, substation 6%, transmission 2%, other 2%; temporary: roads 62%, staging 30%, substation and transmission construction 6% (23 and 17 projects with detail) | same, Tables 2-3 p. 13 | reported |
| L10 | Wind, by prior land cover | permanent direct 0.24 ± 0.28 ha/MW on row crops, 0.24 ± 0.15 pasture, 0.36 ± 0.22 forest; temporary 0.87, 0.59 and 1.11 | same, Table 7 p. 18 | reported |

Converting L4 to AC at an inverter loading ratio of 1.3 [A] gives about **3.6 acres/MWac of array for fixed tilt and 5.5
for tracking**, against Ong's 5.8 and 9.0 for plants built before 2013. Denholm's wind projects mostly used turbines
under 3 MW built before 2009; the average new U.S. turbine was 3.2 MW in 2022 (Jones and Li 2024, pp. 1-2, citing LBNL).
Per-MW wind areas from newer projects were not found in a primary source in this session [A: L7-L8 kept as they are].

### 9b. Runoff from solar sites

**What the studies say.**

- **Panels over established grass change little; bare ground or gravel changes a lot.** A cell model of panel rows on
  grass (B soil, 1% slope, 2-hour 25-year storm) gives a runoff volume 0.35% higher and a peak 0.31% higher than the
  same grass without panels. Gravel under the panels: volume +7%, peak +73%; gravel under the panels with healthy grass
  between rows: volume +4%, peak +42%; bare ground under and between the panels (poor upkeep): volume +7%, peak +72%;
  bare ground between rows: peak about +100%, as with gravel or pavement under the panels and patchy grass or bare
  ground between them. Water dropping off a panel edge can carry "nearly 10 times" the kinetic energy of rain on open ground, so drip lines erode where soil is
  bare (Cook and McCuen 2013, J. Hydrologic Engineering 18(5):536-541, results and conclusions; a model study, not
  checked against field data).
- **Measured and modeled at five U.S. solar farms**, runoff averaged 13%, 25% and 45% of the 2-, 10- and 100-year
  design storm depths, and runoff with arrays was 14% above the same sites without them; the authors treat arrays as
  disconnected impervious surface (Mulla et al. 2024, Vadose Zone Journal e20335, as summarized by the Chesapeake Bay
  Program's Urban Stormwater Workgroup memo, Oct 11, 2024, pp. 2 and 6, and Pennsylvania DEP's FAQ, p. 6; paper not
  read, UNVERIFIED). Their PV-SMaRT calculator returns a curve number for the whole array area from soil texture,
  depth, bulk density, cover, panel width and spacing, orientation and slope (PA DEP FAQ, pp. 6-7).
- **Effective imperviousness of the array area** from SWMM and the PV-SMaRT calculator, averaged and rounded, HSG C,
  2-hour storms: native vegetation **10% with rows parallel to the contours, 20% diagonal, 45% perpendicular** (ranges
  under 2% to 58%); gravel between and under panels **50%, 60% and 75%** (37% to 90%) (Earles, Olson and Howard 2023,
  memorandum to the Mile High Flood District, Table 4 p. 8 and Table 7 p. 10). Roads and equipment pads are added on
  top by area.
- **Soils after construction run wetter.** Grading and heavy equipment compact the soil and strip organic matter; a
  common adjustment is to raise the hydrologic soil group one letter (B to C) when picking curve numbers, which
  Virginia DEQ requires during development and stabilization (Chesapeake Bay Program memo, 2024, pp. 1 and 4-5, citing
  Daniels et al. 2024 and DEQ GM 22-2012; Virginia's memo not read, UNVERIFIED). The same memo finds no study of runoff
  quality from solar sites (p. 1).

**State guidance** (all treat the panels as disconnected impervious surface when the ground under and between them is
vegetated and runoff stays as sheet flow; none treats gravel the same way):

| State | What it says | Source |
|---|---|---|
| Pennsylvania | Vegetation under and between panels, preferably meadow, at 90% perennial cover; row gap at least the panel width; sites that meet the site restoration criteria (slopes 10% or less) leave the array area out of the stormwater analysis, others use PV-SMaRT curve numbers for it; access roads, gravel drip edges and buildings are computed separately; footings and posts need not be counted. Worked example: a shallow (20 in) silt loam on a 10% slope gives CN 92 for the array area | PA DEP, Solar Panel Projects FAQ, Version 1.3, Feb 19, 2026, pp. 4-10, 12-13 |
| Ohio | Disconnection over deep-rooted grasses and forbs at a disconnection length of 2 × the panel's horizontal width, 1:1 panel to gap; soils in good hydrologic condition; not allowed over gravel or hard surfaces; roads and buildings managed separately | Ohio EPA, Post-Construction Stormwater Management for Solar Panel Fields, July 2024, pp. 1-2 |
| Maryland | By statute (2012) only the foundation or base of a panel is impervious; access roads, pads and sheds within the limit of disturbance are; a splash pad or matting at the drip line; the whole work area is in the limit of disturbance even without grading | MDE Technical Memorandum #8, Mar 30, 2018, p. 1 |
| New York | Arrays "may be designed to be disconnected impervious area" depending on table height, spacing, slope, soils and cover; the leading drip edge is the case to model | NYSDEC letter to the state solar industry association, Oct 23, 2024, pp. 1-2 |
| North Carolina | Panels are impervious; disconnection length at least 80% of panel width; gravel is built-upon area | NCDEQ Stormwater Design Manual, E-6 Solar Farms, from search results; UNVERIFIED |
| Minnesota | A disconnected impervious credit method for the water quality volume; gravel paths and roads are impervious | MPCA Minnesota Stormwater Manual solar pages, from search results; UNVERIFIED |
| New Jersey, Michigan | No solar-specific stormwater guidance found from EGLE; New Jersey's not read | — |

**Curve numbers for the parts of a solar site** (TR-55, USDA NRCS 1986, Table 2-2a p. 2-5 and Table 2-2c p. 2-7;
soil group B, with C in brackets):

| Surface | CN, B [C] | Use |
|---|---|---|
| Meadow, continuous grass, protected from grazing | 58 [71] | established native cover, little traffic |
| Open space, good condition (grass cover over 75%) | 61 [74] | mowed turf, well kept |
| Open space, fair (50-75%) | 69 [79] | patchy cover, or compacted soil |
| Newly graded areas, no vegetation | 86 [91] | bare ground under panels or in drive aisles |
| Gravel roads | 85 [89] | access roads, gravel drip edges, gravel under panels |
| Paved, roofs | 98 | inverter and transformer pads, substation slab, buildings |

### 9c. Construction

- **Permits.** Construction stormwater coverage under an NPDES permit is required at one acre of disturbance or more,
  including smaller parts of a larger common plan (40 CFR 122.26(b)(14)(x), five acres and up, and (b)(15), one to
  five); the construction and development guidelines require controls to minimize exposed soil, compaction and
  sediment discharge and to preserve topsoil (40 CFR 450.21(a)). Maryland counts a solar site's whole work area as
  disturbed even without grading (MDE TM #8, p. 1). Michigan's Part 91 and permit-by-rule are already in
  `runoff.PARAMS["construction"]["permits"]`.
- **Sediment.** No measured sediment yield from solar or wind construction was found. Modeling studies find solar
  development raises erosion: 21-75% during construction and 25-76% in operation on a hilly site (Liu et al. 2023,
  Water Resources Research 59:e2023WR035067), and cumulative sediment load up 12-30% at 15-30% solar conversion of a
  small basin (Mier-Valderrama et al. 2024, International Soil and Water Conservation Research 12(2):432-445); both as
  summarized in the Chesapeake Bay Program memo (2024), pp. 5-6; papers not read, UNVERIFIED. So the
  packages' construction yields (`runoff.construction`, gross erosion 30-200 t/acre-yr × delivery 0.1-0.33, EPA MM8
  and measured active sites) remain the basis, applied to the bare share of the disturbed area [A].
- **Dust control water.** Klise et al. (2013) give 1.3-5.7 AF/MW in the peak construction year in the desert Southwest
  (K1). No figure for humid climates was found; there dust control is intermittent and the desert figure is an upper
  bound [A].
- **Wind turbine foundations.** A typical foundation drawing in a 2017 state utility commission siting docket gives 505
  cubic yards (386 m³) of concrete per turbine (read this session: it confirms the top of K5's range; K5's 10,000-18,000
  gal of mix water is superseded below). A foundation for a modern onshore turbine typically takes about 1,000 m³ of
  concrete and 200 tonnes of steel (Carneiro, Mathern and Olsson 2022, Nordic Concrete Research Symposium, p. 1,
  citing a Swedish source). Spread
  foundations designed for a 140 m tower at a seismic California site hold 1,015 m³ (tapered) and 1,334 m³ (circular)
  of ready-mix concrete (Jones and Li 2024, Wind Energy e2947, Table 2). Mix water at 160-190 kg per m³ of concrete [A:
  ordinary structural mixes; the mix tables were not read] gives **about 16,000-50,000 gal per turbine** for 386-1,000
  m³, before curing, washout and road dust control [derived, A].

### 9d. Recommended parameter ranges

| Parameter | Low | Central | High | Basis |
|---|---|---|---|---|
| PV array area, tracking, acres/MWac | 4.5 | 5.5 | 9.0 | L4 at ILR 1.3 [A]; Ong's 9.0 as high |
| PV array area, fixed tilt, acres/MWac | 3.0 | 3.6 | 5.8 | same |
| PV fenced or total area, acres/MWac | array ÷ 0.85 | array ÷ 0.7 | 10 | L5's 69% example [A]; L1-L3, L6 |
| Roads, inverter and transformer pads, substation, share of fenced area | 0.02 | 0.04 | 0.10 | [A]; Pennsylvania's worked example uses 10% (FAQ #12, p. 13) |
| Effective impervious share of the array area, vegetated, rows parallel / diagonal / perpendicular to contours | 0.02 / 0.02 / 0.20 | 0.10 / 0.20 / 0.45 | 0.35 / 0.40 / 0.58 | MHFD Table 4 (HSG C, 2-hour storms) |
| Effective impervious share of the array area, gravel under and between panels | 0.37 | 0.60 | 0.90 | MHFD Table 7 |
| Pervious cover under and between panels, storm CN (soil group B) | 58 (meadow) | 69 (open space, fair, for compaction) | 86 (bare) | TR-55; one soil group up for compaction [A, after Virginia DEQ] |
| Pervious cover, Simple Method Rv | turf, 0.20 on B | turf, one soil group up [A; Runoff Reduction memo Table 4, C value not read here] | — | `runoff.PARAMS["rv"]` |
| Roads and pads, storm CN / Simple Method | gravel 85 | gravel 85, paved pads 98 | 98 | TR-55; Rv 0.95 as impervious [A: Maryland, North Carolina and Minnesota count gravel as impervious] |
| PV construction, disturbed area | array area | fenced area | fenced area | MDE TM #8 |
| PV construction, bare share of the disturbed area in the season | 0.3 | 0.6 | 1.0 (mass grading) | [A] |
| PV construction, duration, years | 0.5 | 1 | 1.5 | [A] |
| PV dust control water, one-time, AF/MW | 0 | 0.5 [A] | 5.7 | K1 (desert peak year as high) |
| Wind total project area, ha/MW | 12 | 34.5 | 57 | L7 (mean ± 1 s.d. rounded; 80% of capacity within 10-50) |
| Wind permanent direct area, ha/MW | 0.06 | 0.3 | 0.6 | L8; p. 11: 0.06 to 2.4 across projects, 80% below 0.4 |
| Wind temporary construction area, ha/MW | 0.1 | 0.7 | 1.3 | L8 |
| Wind permanent area, impervious share | 0.8 | 1.0 | 1.0 | gravel roads and pads counted impervious [A] |
| Wind foundation concrete, m³ per turbine | 386 | 700 [A] | 1,334 | 9c |
| Wind foundation mix water, gal per turbine | 16,000 | 30,000 [A] | 67,000 | 9c at 160-190 kg/m³ [A] |

How these meet the code: for PV, `imp` = effective impervious share × array share of the fenced area + roads and pads
share, `cover` = turf (or one soil group up when the code takes soil groups), `acres` = fenced area, `before` = the
land as it is; for storms, `impervious` the same and `cn_pervious` from the table. For wind, `acres` = the permanent
direct area at `imp` near 1 on land that otherwise stays as it was, so the change in runoff is that small area's.
Construction sediment = `runoff.construction(disturbed acres × bare share)` for the season.

**What could not be sourced:** measured runoff or sediment from operating or under-construction solar sites (none
published, per the Chesapeake memo); the share of a PV site in roads and pads; per-MW land for wind projects built
since 2009; dust control water outside the desert Southwest; concrete mix water per m³ from a read source; and
Michigan solar stormwater guidance.

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
- 40 CFR Part 423, Steam Electric Power Generating Point Source Category (§§ 423.10, 423.11, 423.15, 423.17), eCFR
  current text as of Nov 1, 2026, via the eCFR versioner API.
- U.S. EPA (2015). Technical Development Document for the Effluent Limitations Guidelines and Standards for the Steam
  Electric Power Generating Point Source Category. EPA-821-R-15-007.
  https://19january2021snapshot.epa.gov/sites/static/files/2015-10/documents/steam-electric-tdd_10-21-15.pdf
- U.S. EIA (2025). Form EIA-860, 2024 data: Schedule 6 Part D cooling systems (`6_2_EnviroEquip_Y2024.xlsx`),
  generators (`3_1_Generator_Y2024.xlsx`) and the form instructions; Form EIA-923, 2024 Schedule 8D cooling system
  information and the 2024 cooling detail file. Used in aggregate only (§8b).
- Environmental Integrity Project (2026). The Power Behind AI. July 1, 2026.
  https://environmentalintegrity.org/wp-content/uploads/2026/06/EIP_Report_ThePowerBehindAI_7.1.26.pdf
- Ong, S., Campbell, C., Denholm, P., Margolis, R., and Heath, G. (2013). Land-Use Requirements for Solar Power Plants
  in the United States. NREL/TP-6A20-56290. https://www.osti.gov/servlets/purl/1086349
- Bolinger, M., and Bolinger, G. (2022). Land Requirements for Utility-Scale PV: An Empirical Update on Power and Energy
  Density. IEEE Journal of Photovoltaics 12(2). doi:10.1109/JPHOTOV.2021.3136805. Summary slides, Feb 1, 2022:
  https://emp.lbl.gov/sites/default/files/emp-files/land_requirements_for_utility-scale_pv.pdf
- Denholm, P., Hand, M., Jackson, M., and Ong, S. (2009). Land-Use Requirements of Modern Wind Power Plants in the
  United States. NREL/TP-6A2-45834. https://tethys.pnnl.gov/sites/default/files/publications/Denholm_et_al_2009.pdf
- Cook, L. M., and McCuen, R. H. (2013). Hydrologic Response of Solar Farms. J. Hydrologic Engineering 18(5):536-541.
  doi:10.1061/(ASCE)HE.1943-5584.0000530.
  https://www.energy.gov/sites/default/files/2024-08/CFE%20CookMcCuen2013Hydrologic-Response-of-Solar-Farms.pdf
- Earles, A., Olson, C., and Howard, M. (2023). Determination of Solar Panel Field Runoff Coefficients. Memorandum to
  the Mile High Flood District, Oct 13, 2023.
  https://mhfd.specialdistrict.org/files/3ce3b64e3/TECHNICAL-MEMORANDUM-DETERMINATION-OF-SOLAR-PANEL-FIELD-RUNOFF-COEFFICIENTS-2023.pdf
- Chesapeake Bay Program, Urban Stormwater Workgroup (2024). Evaluating Options for Relative Land Use Loading Rates
  from Solar Development Sites. Memo, Oct 11, 2024, with annotated bibliography.
  https://dev.chesapeakebay.net/files/documents/MEMO_Relative-Loading-Rates-from-Solar-Development_2024-10-15-135203_qbgk.pdf
- Pennsylvania DEP (2026). Chapter 102 Permitting for Solar Panel Projects, Frequently Asked Questions, Version 1.3,
  Feb 19, 2026. https://files.dep.state.pa.us/water/BPNPSM/StormwaterManagement/ConstructionStormwater/Solar_Panel_Farms_FAQ.pdf
- Ohio EPA (2024). Post-Construction Stormwater Management for Solar Panel Fields. July 2024.
  https://dam.assets.ohio.gov/image/upload/epa.ohio.gov/Portals/35/storm/Guidance%20on%20Post-Construction%20Storm%20Water%20Controls%20for%20Solar%20Panel%20Arrays.pdf
- Maryland Department of the Environment (2018). Technical Memorandum #8, Solar Panels. Mar 30, 2018.
  https://stg-mde.maryland.gov/programs/water/StormwaterManagementProgram/Documents/Technical%20Memorandum%20No.%208%20-%20Solar%20Panels.pdf
- New York State DEC (2024). Letter to the New York State Energy Industries Association on solar development and the
  construction stormwater general permit, Oct 23, 2024.
  https://nyseia.org/_files/ugd/a89dc9_ef24fb0a76cb44d691a8e196636bf382.pdf
- USDA NRCS (1986). Urban Hydrology for Small Watersheds, TR-55, 2nd ed., Tables 2-2a and 2-2c.
- 40 CFR 122.26(b)(14)(x) and (b)(15), and 40 CFR 450.21, eCFR current text as of Nov 1, 2026.
- Carneiro, E., Mathern, A., and Olsson, N. (2022). Potential improvements in the life-cycle performance of support
  structures for onshore wind turbines: an interview study in Sweden. Proceedings of the XXIV Nordic Concrete Research
  Symposium. https://research.chalmers.se/publication/532015/file/532015_Fulltext.pdf
- Jones, K. E. S., and Li, M. (2024). Life Cycle Assessment of Additively Manufactured Foundations for Ultratall Wind
  Turbine Towers. Wind Energy, e2947. doi:10.1002/we.2947
- A typical wind turbine foundation drawing in a 2017 state utility commission siting docket (the docket appendix
  listed under the secondary sources below, now read).

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
- Moore, W. E., and Rittof, T. J. (2007). ZLD Today, Part 1: Matching Water Treatment Options to Power Plant
  Requirements. Water Technology, March 1, 2007 (trade article, read through a summary).
- Simple-cycle evaporation ponds in the arid West: one Nevada NPDES permit fact sheet, from search results; not read.
- Mulla, D., Galzki, J., Hanson, A., and Simunek, J. (2024). Measuring and modeling soil moisture and runoff at solar
  farms using a disconnected impervious surface approach. Vadose Zone Journal e20335 (through the Chesapeake memo and
  the PA DEP FAQ).
- Liu, H., et al. (2023). Effect of solar farms on soil erosion in hilly environments. Water Resources Research
  59:e2023WR035067; Mier-Valderrama, L., et al. (2024). International Soil and Water Conservation Research
  12(2):432-445; Daniels, L., et al. (2024), Virginia solar site white paper; Virginia DEQ GM 22-2012 (all through the
  Chesapeake memo).
- Utility-scale solar land use in the Western Interconnection, Communications Earth & Environment (2025),
  doi:10.1038/s43247-025-02862-5, through pv magazine USA, Dec 15, 2025.
- NCDEQ Stormwater Design Manual, E-6 Solar Farms, and MPCA Minnesota Stormwater Manual solar pages (search results).
