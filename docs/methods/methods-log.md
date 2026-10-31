# Methods log

A dated record of method decisions: what was decided, why, what else was considered, and what is still open. It is the
long form. The short forms are the two-page briefs (`docs/methods/<st>.pdf`) and the methods pages on waterledger.org
(`/methods/`, `/methods/<st>/`, Michigan's `/mi/methods.html`), and they are kept in step with this log.

Layer-by-layer notes for the national tier (places, water supply, wastewater, receiving waters, climate, energy) are in
[national-tier-notes.md](national-tier-notes.md); county water use sources are in [water-use-sources.md](water-use-sources.md).
This log covers decisions that cut across layers, and points there for detail.

## Oct 30, 2026: Michigan builds on GitHub like the other states

`waterledger build-state MI` now downloads Michigan's sources and builds from an empty cache, so its snapshot no longer waits for
a site deploy. EGLE's water-use file, which EGLE will not serve to scripts, is committed in `data/inputs/mi/` with facility names
removed. `waterledger build mi` stays for building from a cache.

Checked against the published files, from an empty cache on GitHub (run 41169694682): `waters` and `power` match apart from the build
date. `estimates` differs in 175 values, all by less than one part in a billion (floating point between macOS and Linux). `places` differs
in three: two water system shares by 0.01 (Bangor, Cedar Springs), and Rogers City's main watershed, Lone Lake-Ocqueoc instead of Lake
Huron. Its center lies in Lone Lake-Ocqueoc in the current boundaries, so the published value was out of date. No water or power estimate
changed. Where a place's center falls in two HUC8s (only Cheboygan), the lowest code is now taken, so the result does not depend on
the order the service returns.

## Oct 29, 2026: one method, many states (3.0.0)

- **Decision.** The method that produced Water Ledger Michigan (model 1.2) is applied to any U.S. state from national
  datasets (design 0002). Michigan keeps its state layers and its ERA5 weather; national-tier states use NOAA ISD
  station records by climate division.
- **Why.** Most of Michigan's inputs have national equivalents (Census places, EPA water systems, CWNS and ECHO plants,
  USGS WBD, EPA ATTAINS, NOAA Atlas 14, HIFLD and EIA-861). A state-by-state build would not scale.
- **Alternatives considered.** ERA5 for every state, as in Michigan: more uniform weather, but larger downloads per state
  and a dependence on a reanalysis service; deferred until the station-distance check (below) is done.
- **Consequence.** Hybrid and evaporative-assist estimates are sensitive to the weather source (station records gave
  4-50% higher values than ERA5 in southern Michigan, 2-5 times at Traverse City and Alpena; cooling towers within 1%),
  so Michigan's and other states' hybrid numbers are not strictly comparable. Every methods page says so.

## Oct 29-30, 2026: data releases and versions

- **Decision.** Each state's inputs are published as a dated, checksummed snapshot at data.waterledger.org (design 0003).
  Code (package semver), numbers (`MODEL_VERSION`) and data (snapshot date) are versioned separately. A manifest records
  the package versions that built a snapshot, its sources and its statewide checks.
- **Oct 30 rebuild.** The Oct 29 snapshots were built before the package version number was raised to 3.0.0, so their
  manifests recorded 2.0.0. All four states were rebuilt with the released 3.0.0 and published as 2026-10-30. Every data
  file has the same content as 2026-10-29 (checked file by file); one file per state (`receiving.json`) differs only in
  the order of its entries. The Oct 29 snapshots were left in place as the record of what 2.0.0 built.
- **Open.** Snapshot files should be written in a fixed order so a rebuild of the same inputs is byte-identical.

## Oct 30, 2026: how the methods are presented

- **Decision.** Each state's brief and methods page has two parts: the overall method, the same text in every state,
  then what is specific to the state (its weather stations, its place types, the agency whose water quality report is
  used, its own layers, and the layers not yet added). States are not described by comparison with Michigan.
- **Why.** A state's methods should stand on their own for readers in that state; the overall method is the reference
  each state departs from. The all-states page keeps one note on Michigan's weather, because that is where readers
  compare states.
- **Detail.** EPA ATTAINS organization codes are shown as agency names (21MICH: Michigan EGLE; 21OHIO: Ohio EPA;
  21VASWCB: Virginia DEQ; TCEQMAIN: TCEQ). Coverage near 100% is shown to one decimal (99.7%, not 100%).

## Oct 30, 2026: state electricity totals and homes (3.1.0)

- **Decision.** `waterledger_data.power.state_retail_mwh` gives all retail electricity sold in a state (EIA-861 Sales to
  Ultimate Customers, Parts A, B and D, as EIA totals a state; Part C, delivery only, is left out because that energy is
  counted by its seller). `residential` gives residential customers and average monthly use per home from the same file.
- **Use.** The pages compare a campus's electricity with the state's retail total and express it in homes at the state's
  average use. 2025 averages: Michigan 635 kWh a month, Ohio 874, Virginia 1,067, Texas 1,113.
- **Open.** Michigan's page uses 618.2 kWh (EIA Table 5A, 2024), not the EIA-861 2025 figure. Moving Michigan to the
  shared format should also move it to this function, which is a number change to record in the methods changelog.

## Oct 30, 2026: page data for national-tier states

The pages for Ohio, Virginia and Texas read the same five files as Michigan's (estimates, places, map, waters, power),
written from each state's snapshot by Northline's `engine/products/state_data.py` (website code stays out of the
packages). Decisions that affect what readers see:

- **Map projection.** Equirectangular, x scaled by the cosine of the state's mid-latitude, with each map scaled to the
  same width as Michigan's. The file records km per map unit (Ohio 1.09, Virginia 2.23, Texas 3.73; Michigan 1.852), so
  distances drawn from map units are right at any latitude. Checked: Columbus to Cleveland within 2% of the great-circle
  distance; page distances to sewer plants within 1.5 km of the package's.
- **Counties.** County outlines from the snapshot's Census boundaries, simplified (Douglas-Peucker), with slivers under
  0.5 square map units dropped. Virginia's independent cities are drawn as county equivalents. Census county boundaries
  include water, so Ohio's lake counties extend into Lake Erie.
- **Downstream.** The next HUC12 downstream is rebuilt from consecutive entries of the snapshot's downstream paths (no
  conflicts in Ohio, Virginia or Texas). Whether a HUC12 was assessed is not in the snapshot and is not shown.
- **Regions.** Climate divisions are named "Division N" with their station; NOAA's division names are not yet in the
  data.
- **Electricity choices.** The grid regions serving the state, by the names readers know (ERCOT, SPP, PJM, MISO, LG&E and
  KU, TVA), each at its 2022 consumption intensity (Siddik et al. 2024), plus generic gas and wind and solar factors
  (Macknick et al. 2012). There is no state fuel mix. The starting choice is the grid region of the utility serving most
  of the place.
- **Delivery-only utilities.** Texas transmission and distribution utilities (Oncor, TNMP) report no EIA retail sales;
  the page names them and says why there is no load comparison.
- **Stand-ins.** The runoff and water quality calculations use Michigan's post-construction standard and parameter
  sources for every state, labeled [A] as a stand-in. Michigan's own rules (Part 327, WWAT, Part 22 septic tiers, Rule 57,
  Rule 60, Rule 75, Part 5) are not cited for other states; their pages say state rules are not yet reviewed.
- **Size and site buttons.** Michigan's buttons use Michigan project examples; other states use round sizes, labeled
  [A].
- **Layers not yet available** are listed in the data (`state.layers`) and the pages say so in one line instead of
  showing an empty card: county water use (until the layer below), household wells, coldwater streams, lake-source
  cooling, state rules, golf.

## Oct 30, 2026: county water use

- **Decision.** A national floor for every state, USGS's revised 2015 county estimates (Sleckman, Ross and Cook 2026,
  doi:10.5066/P14Q6AVK), labeled as estimates; each state's own figures replace it where Water Ledger reads them: Ohio
  ODNR facility registration (reported withdrawals, 2024), Texas TWDB Water Use Survey (TWDB's "use", 2024), Virginia
  DEQ locality totals (reported withdrawals, excluding power, 2024). Michigan keeps EGLE.
- **Why.** A county comparison is one of the most useful numbers on the page and in a Water Review, and readers trust
  the figures their own state publishes; but those differ in basis, so every figure carries its source, year and basis.
- **Caveats recorded.** Withdrawals are counted where water is taken, not where it is used (Loudoun withdraws about 7-17
  Mgal/d but its homes receive about 27 from public supply), so pages should show both. Data centers are not a category
  in any state's reporting; they sit inside public supply or municipal use. "Use" differs: Ohio and Virginia report
  gross withdrawals; Texas reports intake minus sales and counts power plants as consumption only.
- Sources, structure and test values: [water-use-sources.md](water-use-sources.md).

## Oct 30, 2026: assumptions checked against primary sources for publication (model 1.3)

Every parameter behind the electricity figures, the power-plant water and the staff water was traced to a primary
source, read at the cited table or page, and either confirmed, re-cited or changed. Where no single source settles a
value, the range spans the published figures and central values come from weighted averages (weights stated). Model
1.3 lowers cooling-tower and hybrid water and electricity by about 13% at the median and staff water by about 9% at
300 MW (stored two-year test weather, 40 runs); closed-loop top-ups are unchanged.

**Utilization: average IT draw / IT capacity, 0.60-0.90 to 0.50-0.80.**
- The old range cited LBNL 2024, which does not give it. Three ratios are easy to confuse: (a) average over a site's
  own peak (load factor); (b) average over interconnection or nameplate capacity; (c) average IT draw over IT capacity,
  which is what the model needs, since announced MW are usually IT ("nominal") capacity.
- EPRI (2026), *Powering Intelligence 2026*, p. 14: measured hourly load shapes; average annual load 75% of nameplate
  for a large hyperscale facility and 57% across co-location facilities (b); 94% and 88% of each site's own peak (a).
  Nameplate there is nominal IT capacity times PUE, so the 75% is close to (c).
- IEA (2025), *Energy and AI*, Annex Table A.1 (world): hyperscale load factor 53-56% in 2020-2024, 50-52% in 2030
  (166 TWh / (36 GW x 8,760 h) = 0.53, i.e. average over installed capacity).
- LBNL 2024, p. 6: "an average capacity utilization rate of 50%" to turn energy into power (b); pp. 20-27 server
  parameters: AI servers draw about 70% of rated power when operating (60-80%), idle 20%; operating time 80% for
  training and 40% for inference; hyperscale conventional servers 45-50%. These give about 0.6 (training) and 0.4
  (inference) of rated power. LBNL 2025 Update (LBNL-2001758), pp. 9-10: interconnection utilization "estimated to be
  around 50%"; inference falls to about 20% by 2030.
- Tariff minimum-demand floors (AEP Ohio 85%, Dominion GS-5 60-85%, Consumers Energy 80%, MPSC U-21859) bill against
  contract capacity; they bound expectations from above and are not measurements.
- **Decision:** 0.50-0.80, uniform, central 0.65: the low end from IEA and LBNL's mixed AI fleet, the high end from
  EPRI's measured hyperscale site. It describes a campus at full build-out; EPRI's ramp (20% of capacity in the first
  year, plus 20% a year) means early years run lower. 0.90 is a load-over-peak figure and was dropped.
- **Rule recorded:** when the announced MW is utility or interconnection capacity, divide by the design's PUE first
  (the calculator already does this for utility contracts) or apply 0.45-0.75 to facility power directly; never
  utilization times PUE on interconnection MW.

**PUE by cooling design: confirmed, re-described.** Values are read from LBNL 2024 Fig. 4.4 (p. 46), large-scale
facilities, simulated annual PUE over U.S. climates (figure-read, about +/-0.01): liquid-cooled IT with dry coolers
about 1.10 (whiskers 1.04-1.16); dry cooler with adiabatic assist and air-cooled chiller about 1.20 (1.06-1.34);
airside economizer with adiabatic cooling and water-cooled chiller about 1.14 (1.02-1.27); waterside economizer with
water-cooled chiller (cooling towers) about 1.12 (1.03-1.22). Closed loop (1.07-1.24, central 1.15) spans the first
two; LBNL has no large-scale waterless row for air-cooled IT, so the upper bound uses the adiabatic-assist row, which
uses a little water. Independent checks: IEA 2025 Table A.1 hyperscale PUE 1.14 (2024), 1.10 (2030); Google's
measured fleet-wide trailing-twelve-month PUE 1.09 in 2025, 1.08-1.11 at its cool-climate sites; Microsoft (2024)
describes its zero-water design's energy cost as "a nominal increase in our annual energy usage". The common
expectation that evaporative cooling saves much electricity holds for mid-size chiller plants in LBNL's figure
(air-cooled chiller about 1.8, water-cooled chiller about 1.5) but not for large economizer-based campuses.

**Power plant water for Michigan's mix: values confirmed, sources corrected, withdrawals added per supply.**
- Michigan net generation 2024: 124.2 TWh (EIA Michigan Electricity Profile 2024, Table 5): natural gas 44.9%, nuclear
  21.2%, coal 20.7%, wind 7.9%, solar 1.5%; 2025 (preliminary) 128.5 TWh, similar shares.
- Consumption. Macknick et al. (2012) medians (Table 2, p. 6) weighted by the 2024 and 2025 mixes give 239 gal/MWh
  (0.90 L/kWh). EIA-923 Schedule 8D 2024 plant reports (deduplicated by plant, cooling system and month; divided by all
  Michigan net generation) give 0.60 L/kWh after setting aside Midland Cogeneration Venture (reported 25,542 Mgal
  consumed of 28,055 withdrawn, about 2,370 gal/MWh; EGLE shows 586 Mgal withdrawn), with Cook, Campbell, Belle River,
  Dearborn and Greenwood reporting zero consumption; filling those with Macknick's once-through medians gives 0.96, and
  applying Monroe's own reported consumed share (1.49% of withdrawal) to all once-through plants gives 1.19. Measured
  tower-cooled combined-cycle plants (Blue Water, Covert, Zeeland, Jackson) consumed about 189 gal/MWh, inside
  Macknick's 130-300. **Decision:** 0.9 L/kWh (238 gal/MWh), range 0.6-1.2 (was 0.68-1.31). Peer et al. (2019) give
  consumption by eGRID region including upstream fuel water (RFCM 1.3 m3/MWh), a different boundary; dropped as a
  source of this range.
- Withdrawal. EIA-923 2024: 2,001,748 Mgal, 61.0 L/kWh, about 1% consumed. EGLE 2025 power-generation withdrawals
  (1,904.6 billion gal) over EIA's 2025 generation: 56.1 L/kWh. Macknick Table 3 medians weighted by the mix: 54.9
  (2024) and 58.0 (2025). **Decision:** 57 L/kWh (15,060 gal/MWh), range 50-61, 98-99% returned. The earlier citation
  was wrong: 57 is MISO's 2022 load-weighted value in the Siddik et al. (2024) dataset (57.07; Water Resources Research
  60(12), e2024WR038350; HydroShare v1.1), which now serves only as a cross-check and for the "MISO average" option.
- Plant cooling (EIA-860, 2024): once-through: Cook (Lake Michigan), Monroe (Raisin River), Campbell, Belle River (St.
  Clair River), Dearborn Industrial; natural-draft towers: Fermi 2; induced-draft towers: Blue Water, New Covert,
  Zeeland, Jackson; dry: Indeck Niles; ponds: Midland Cogeneration, Greenwood. Cook, Covert and Indeck Niles are in
  PJM, not MISO.
- Per supply (gal/MWh, consumed / withdrawn, Macknick Tables 2 and 3): gas combined cycle with towers 205 (130-300) /
  255 (150-283); Michigan coal, once-through 250 (100-317) / 36,350 (20,000-50,000); Michigan nuclear weighted by 2024
  generation (Cook 68.6% once-through, Fermi 31.4% towers; was two-thirds and one-third) 396 (251-540) / 30,770
  (17,400-41,980); wind and solar weighted by Michigan's 2024 generation (wind 7.9%, solar 1.5%; wind 0, PV 1 with
  0-5; withdrawal equals consumption for both, Macknick p. 6) 0.2 (0-0.8). Was 1 (0-5), which treated the mix as all
  solar.

**Staff water: gallons per person now cited; people per MW re-cited.**
- Basis: people = permanent headcount (employees and on-site contractors), gallons per person per calendar day. The
  sources count headcount, not people on site at once, and give water per workday or shift.
- Gallons per person: 15-30 (no source) to 10-30. U.S. EPA (2002) Onsite Wastewater Treatment Systems Manual,
  EPA/625/R-00/008, Table 3-4, p. 3-7 (from Crites and Tchobanoglous 1998): office or industrial building, 7-16 gal
  per employee per day, 13 typical (with EPAct 1994 fixtures), about 9 per calendar day for a five-day week. Michigan
  Department of Public Health (1994) Criteria for Subsurface Sewage Disposal, App. C, Table 1: factories 35 gal per
  person per shift (a design value with margin), about 25 per calendar day. Gilroy Data Center (City of Gilroy, NOP
  2022 and project fact sheet): 1,800 gal/day domestic for about 50 full-time employees, about 30-36. Gleick et al.
  (2003, Pacific Institute, App. E, Table E-2) model office restroom plus kitchen use at about 15 per employee-day.
  The range runs from typical measured use to applicant and design values.
- People: core 20-60 kept; JLARC (2024) Report 598, p. 13, a typical 250,000 sq ft data center "may have approximately
  50 full-time workers", about half contractors; Gilroy about 50 full-time plus up to 74 contractors as needed. MCL
  205.54ee(10)(e)(v)'s 30-job minimum is an incentive condition and is no longer cited as evidence. Per MW 0.1-0.5
  kept, now cited to announced campuses (permanent jobs / announced capacity): Meta Richland Parish, more than 500
  operational jobs at 5 GW (0.1; 0.25 at the earlier 2 GW); Meta El Paso, more than 300 at 1 GW (0.3); Saline
  Township Stargate, 450+ onsite at about 1.4 GW (0.32); Gilroy, 50 at 98 MW (0.5). JLARC gives no per-MW figure; its
  statewide average (more than 8,000 jobs over about 5,050 MW, about 1.6 per MW) covers older, smaller buildings.
  Microsoft Mount Pleasant (about 800 jobs at about 900 MW, secondary reports) is above the range.
- Share used up: 0.05-0.15 kept; Shaffer and Runkle (2007), USGS SIR 2007-5197, Table 9, p. 16: commercial, Great Lakes
  Basin (n = 29), median 10%, quartiles 8-15%, range 4-26%.
- Applicant figures (Lowell, about 2.2 million gal/yr excluding cooling; Crusoe, about 2 million gal/yr for a 200 MW
  building) are well above sanitary rates per person; they include maintenance and washdown. That belongs in its own
  term, not in gallons per person (open).

**Homes.** Michigan's average residential use moves from 618.2 kWh/month (EIA Table 5A, 2024) to 634.9 (EIA-861 2025,
Parts A, B and D; 4,538,056 customers), the function the other states use; about 3% fewer homes per MW.

**Every state: power-plant water from plant data (supersedes the Michigan values above).** Andrew's rule (Oct 30): an
error found in one state is checked and fixed in every state, to the same standard; values may differ by state.
- The national tier used Siddik et al.'s 2022 balancing-authority values (`grid_water_2022.csv`; every row reproduces
  the dataset, load-weighted, to four decimals: consumed_excl_hydro = WCI_NH, withdrawn_excl_hydro = WWI_NH, Siddik
  Table 3, p. 8). Against 2024 plant data aggregated by balancing authority, they run high in most large eastern
  regions (consumed, L/kWh: PJM 1.30 vs 0.95, MISO 1.57 vs 1.04, SOCO 1.52 vs 1.20, NYIS 0.63 vs 0.39, ISNE 0.63 vs
  0.43) and agree for ERCOT (0.73 vs 0.77); 2022's larger coal share, imports and fuel-type defaults for non-reporting
  plants are candidate causes, not resolved.
- **Decision.** Every state uses one method (`docs/methods/power_water/`, table `state_power_water_2024.csv`): EIA's 2024
  cooling water data by plant over the state's 2024 net generation; flagged reports (consumption above withdrawal or
  1,500 gal/MWh; zero consumption at once-through or pond plants; cooling-reservoir circulation reported as withdrawal,
  over 25,000 gal/MWh at tower or pond plants) replaced by Macknick et al. medians, 181 plants nationally, each listed;
  blended with the main balancing authority's plant-based value by the state's net interstate import share (EIA State
  Electricity Profiles 2024, Table 10; 0 for net exporters); range = min and max over reported (where no plant is
  flagged), adjusted, Macknick bottom-up, blended and Siddik's 2022 value. Results (consumed; withdrawn, L/kWh):
  Michigan 0.94 (0.76-1.57); 58.7 (54.8-58.8). Ohio 1.03 (0.96-1.30); 24.6 (21.2-52.3), 13% imported. Virginia 0.59
  (0.42-1.30); 51.2 (48.4-56.3), 31% imported, with North Anna, Surry and Chesterfield reporting zero consumption.
  Texas 0.78 (0.73-0.78); 19.1 (13.2-55.0). Michigan's earlier 0.9 and 57 are replaced by its table values so every
  state follows the same rules.
- **Texas withdrawal.** EIA's reported 49 L/kWh counts circulation through cooling reservoirs (Comanche Peak's Squaw
  Creek, South Texas Project's main cooling reservoir, Martin Lake and others) as withdrawal; the adjusted 19 replaces
  those plants with Macknick's pond medians (makeup water). The range keeps Siddik's 55. The same rule applies to pond
  plants in every state.
- **Not included.** International imports (Vermont from Quebec, about 108% of its use; Michigan 1.0 TWh net from
  Ontario); Alaska and Puerto Rico (no main balancing authority; no figure).
- **Wind and solar** is weighted by each state's own 2024 wind and solar generation (`wind_solar(pv_share)`; Ohio 59%
  PV, Virginia 99%, Texas 25%, Michigan 16%), no longer Michigan's for every state.
- **Texas places with no grid region (bug).** The service-territory layer lists Oncor, CenterPoint, AEP Texas Central,
  TNMP and Sam Rayburn Municipal Power Agency under control area NOT AVAILABLE, so 475 of 1,481 Texas places had no
  power-plant water; East Kentucky Power Cooperative had the same gap in Ohio and Virginia. Fixed with each utility's
  one RTO in EIA-861 Utility Data 2025 ("Operating in these RTOs"): the four Texas delivery companies to ERCOT, Sam
  Rayburn to MISO, East Kentucky to PJM. Every territory in Texas, Ohio and Virginia now has a region.

**Maintenance and other non-cooling water (new term).**
- Applicant non-cooling figures run well above sanitary use per person. A campus base of 0-2,000 gal/day plus 2-20
  gal/day per MW, 3-15% used up, kept apart from staff water and cooling. No metered figure is published; the range is
  bracketed by applicant projections: Hermantown, MN (Google; city slides Oct 20, 2025 and Aug 17, 2026): loop
  maintenance about 2,000 gal per building a month (low end); Crusoe's 200 MW building, about 2 million gal/yr for
  "employee restrooms, kitchens, routine maintenance, and equipment washdowns", less its staff water, about 23 gal/day
  per MW (high end). Checked, staff plus maintenance at middle values: Crusoe 5,500 gpd vs about 5,200; Saline Township
  (about 1.4 GW; 20,000 gpd projected; 450 jobs in three shifts of 150) vs about 22,000; Microsoft at Tyrone, GA
  (letter to the mayor, Mar 17, 2026: 2,000 gpd per building, "domestic uses only") within range; Gilroy (ESA water
  supply assessment, Aug 2023, Table 3-3: 1,800 gpd domestic and 2,700 gpd irrigation) fits without irrigation.
  Hermantown's 30,000-50,000 gpd campus figure (cafeterias, laundry, showers, irrigation) is above the model and is
  treated as an amenity-heavy upper bound, not a calibration point.
- Corrections: the "2,000 gallons a day per building" figure attributed to Microsoft at Gaines is from its Tyrone
  letter; Lowell's 2.2 million gal/yr has no primary source yet.
- Landscape irrigation is left out: it is site- and climate-specific (Gilroy's is California's estimated-water-use
  method). Used up share for irrigation would be about 90% (Shaffer and Runkle, Table 9).
- At 300 MW the median non-cooling water (staff plus maintenance) is about 7,000-7,500 gal/day, about 9% used up.

**Cooling physics.** The parameters marked estimates were traced (`physics.py` comments give each source):
- Derived from sourced inputs (no published value exists): heat factor with economizer 1.03-1.10 (was 1.08 top), from
  Lei and Masanet's Table 3 component losses (UPS 90-99%, distribution 0-2%, fans 1.4-9.2% of IT; see the source check below), with the top set by measured large-campus overhead; economizer and
  chiller wet-bulb limits 5-12 and 14-22 °C (were 8-12 and 16-20), from chilled-water supply 12.8-18 °C (FEMP Data
  Center Design guide, 2024, p. 17) less tower and heat-exchanger approaches (Lei Table 3), split at their midpoints
  so each draw ramps upward; FEMP (p. 19): economizers suit climates below 55 °F wet-bulb for 3,000+ hours a year.
- Re-sourced and changed: evaporative ratio adjustment -0.10 to +0.05 (was +/-0.05), asymmetric because Rutberg et
  al.'s (2011) cubic was fitted to Poppe-model runs at 40 °C inlet water and 60% RH (footnote 7, p. 7) and is applied
  here hourly to cooler tower water and cold hours, where it likely runs high (USGS SIR 2013-5188: +/-5-15%, p. 24;
  +/-18% overall, pp. 28-29); tower range 7-15 °F (Lei Table 3: 4-6 °C); drift 0.0005-0.02% of circulating flow (EPA
  WaterSense at Work 2012, section 6.3: modern eliminators under 0.005%; AP-42 13.4, Table 13.4-1: induced draft
  0.020%); closed-loop volume 2,000-12,000 gal per MW (Crusoe 2026: 1.7 million gal for a 200 MW building; Vantage
  Port Washington: about 11.8 million gal for about 1 GW); hybrid wet-mode start 21-28 °C (US Patent 12,426,214 B1, 2025: 70-95 °F,
  example 82 °F).
- Kept and re-cited: chiller heat factor 1.15-1.25 (FEMP: compressor heat "up to 20%" of heat rejected; COP 5-8 gives
  1.13-1.20); cycles of concentration 3-7 (FEMP BMP #10); loop top-ups 1-5% a year (NIH 2023; the 1% floor is an
  assumption, and poorly kept loops can lose 25% a month).
- Still an assumption [A], to calibrate: hybrid fully evaporative at 30-33 °C. The assist share is replaced (below).
- Method notes for the paper: LBNL and Lei count all tower heat as evaporation (Lei Eq. 5); this model's evaporative
  ratio below 1 gives towers about 10-25% less water than that method. Drift is applied in hybrid hours; the assist design has none (below).
- Effect on the stored test weather, model 1.2 to 1.3 at the median: cooling towers about 16% less water, hybrid about
  28% less, closed-loop top-ups about 60 gal/day per 100 MW (was 30); the non-cooling term adds about 4,500 gal/day at
  300 MW.

**Lei and Masanet: source check (Oct 30).** The published article (Resources, Conservation and Recycling 182: 106323) is closed
access and could not be read: ScienceDirect refuses automated reads, and OpenAlex and Semantic Scholar list no open copy. Values were
checked against its preprint on Research Square (Lei and Masanet 2021, doi:10.21203/rs.3.rs-769999/v1, CC-BY 4.0), which is not on
arXiv; the 2020 Energy paper and arXiv 2006.06819 are other works. Preprint Table 3, large-scale cases: distribution 0-2%, tower
approach 2.8-6.7 °C, heat exchanger approach 1.7-2.8 °C and tower range 4-6 °C match what was cited; fans 1.4-9.2% of IT reproduces from
its CRAH pressure (300-1000 Pa), fan efficiency (65-90%) and air temperature (13.9-19.4 °C) ranges. **UPS 97-99% was wrong:** the table says
90-99% (LBNL 2024 Table 4.3 also 90-99%), and no source for 97-99% turned up. With every term at one end the sum is 1.02-1.22, so the
component sum alone does not give the old top of 1.10. The top stays 1.10 for a different reason, stated now: heat through the water
loop cannot exceed the facility's overhead, and large campuses measure 1.09 (Google 2025) to 1.14 (IEA 2025) with cooling included (LBNL
2024, about 1.12 with towers). No numbers change. To check with library access: the published Table 3 and its numbering (the method
became "hybrid physical-statistical" and 16 climate zones became 15, so renumbering is plausible). Until then these values cite the
preprint.

**Assist design: relabelled and re-sourced (Oct 30).** Microsoft's 85 °F is, in its own words, for "direct evaporative cooling", air
side, not a closed loop with assist, so the design took its start from a different system and its share (0.10-0.30) had no source. It is
now dry coolers with adiabatic pre-cooling (the taxonomy of Masanet 2026, arXiv 2610.04735, Table 2), a physical calculation:
- Evaporated share of the heat = d / (on + rise - T + d), with d = effectiveness x wet-bulb depression, capped at 1. The air flow is what
  carries the heat with the air leaving the coil where it did at the switch point, since fans slow in wet mode (Mokkapati and Das 2026,
  a preprint, describe this operation). At full air flow the share can pass 1 and overstates water.
- Effectiveness 0.70-0.80: EVAPCO (2018, p. 2) measured 72-78% at 400-700 fpm over 10 pads, and none reached 90% in the normal range, against
  supplier claims of 65-97% and ASHRAE's (2016, ch. 41) 70 to over 95% for rigid media. Spray pre-coolers (SCE ET13SCE1020, 20-80%) are
  not modeled.
- Switch point 20-30 °C [A]: no maker publishes one, because it is set when a unit is selected and tuned by its controls (EVAPCO, p. 2; BAC;
  Guentner): roughly the air temperature at which the dry coil alone can no longer hold the leaving fluid temperature. The bottom is Uptime
  Institute's reported 20 °C. The top is our assumption, chosen because a higher switch point means a warmer fluid loop than most
  large sites run; Vertiv's energy-first example, 8 °C, is left out as outside what a water-conscious site would choose. The sensitivity
  analysis shows how much this choice matters.
- Coil air rise 9-13 K [estimate]: read from makers' selection sheets (Thermokey 11.2 K, Kelvion 12.8 K), whose energy balances close, and
  an unverified Guentner sheet at 9 K. Manufacturer selection data is the right kind of source for a design value like this; the copies
  used are on used-equipment listings, so the citation says so.
- Bleed 0-0.5 of evaporation: none for once-through pads (Guentner; Spinazzola 2021), 10-50% for recirculating (SCE, p. 29); ASHRAE's
  5-100% is wider, for water hardness. No drift: pads have no tower drift. A new random stream keeps every other design's draws unchanged.
- Result on the stored test weather: about 0.06 L/kWh used up (0.015-0.14), about the same as hybrid (0.05), so the two overlap rather than
  rank, which makes sense since they are close to the same technology; the test no longer requires assist below hybrid. Mokkapati and Das
  give about 0.05-0.25 L/kWh for arid western cities (my conversion), so a cool climate at the low end is plausible. No operator
  has published water use for an adiabatic dry cooler site. The main calculator does not offer this design; the detailed calculator does.

**Power-plant water: plant data and Siddik et al. combined (Oct 30; `docs/methods/power_water/reconciliation.md`; supersedes the central values and ranges above).**
The two are not independent: both rest on EIA-923 Schedule 8D plant reports, so their gap is mostly data treatment, and averaging the published
values would mix definitions and count those reports twice. Rebuilding Siddik's values from public EIA data reproduces them (consumption r = 0.98,
4.4% weighted error; withdrawal r = 0.93, 8.1%), which assumes rules their paper does not state: non-reporting plants, and plants reporting zero
consumption, take a national fuel-wide average. How much of the load-weighted gap (0.24 L/kWh consumed; 14.5 withdrawn) each cause explains:
screening and zero reports 84% and 56%, Siddik's fill of non-reporters 28% and 24%, year -1% and 20%, imports 4% and -3%, generation data -1% and 4%, residual -14% and -1%. So
the year is not the reason for consumption. Withdrawal's gap in ERCOT is reservoir circulation.
Decision, at Andrew's direction that similar estimates may be combined once they are on the same basis: a lognormal Bayesian update. E1 is the 2024
value plus a new fill of non-reporting steam and combined-cycle generation with Macknick tower medians (about 148 TWh, 3.4% of U.S.; combustion
turbines stay at zero). E2, the prior, is each plant's screened 2022 intensity at 2024 generation, times the ratio of Siddik's published value to our
rebuild of it for the region. Variances come from plant-by-plant differences between years, with 2023 data separating noise from real
change (45% of the two-year difference for consumption, 60% for withdrawal). Weight on 2022 is at most 0.275 for consumption and 0.20 for
withdrawal, and falls to almost nothing where the rebuild does not reproduce Siddik. Range: the 95% interval with shared reporting error (Diehl and Harris's 8% and
24% as a scale [A]), E1, E2 and a Macknick bottom-up; raw Siddik values leave the range, since they measure something else. Results (consumed; withdrawn, L/kWh): Michigan 1.01
(0.74-1.38); 58.5 (38.2-89.6). Ohio 1.06 (0.89-1.25); 24.3 (15.9-37.2). Virginia 0.67 (0.48-0.95); 51.9 (33.9-79.4). Texas 0.77 (0.62-0.94); 19.2 (11.8-31.2). Median change across states
+6.1% and +0.6%, mostly the fill. Assumed constants [A]: error scales 0.35 and 0.5, floor 0.02.
Open: Siddik's HydroShare notebook would confirm the inferred rules; residuals in ISNE, NEVP, DUK and PNM are unexplained; screening
gaps left in place (low tower reports, 15 plants; Sequoyah 2024; Big Stone, South Dakota); Hawaii is weak; Peer and Sanders and Diehl and Harris figures to check against the papers' full text.

**Sensitivity analysis (Oct 30; `docs/methods/sensitivity/`).** Sobol indices (N = 8,192 per design; Saltelli and Jansen estimators, bootstrap
intervals) and Morris screening of every parameter over the stored West Michigan weather, per 100 MW; the non-cooling term at 300 MW.
Repeatable: fixed seed, and a second full run gave byte-identical results files (only the commit and runtime in `run_info.json` differ). Results,
total-order: cooling towers are led by utilization (0.82 on water used up) and the evaporative ratio adjustment; hybrid by its switch
temperature (about 0.85 annually) and assist by its own (0.93), both operator settings, better taken from an applicant or shown as scenarios
than treated as physical uncertainty. The derived heat factors and wet-bulb limits sum to about 0.01 for annual tower water, so they need no
further work. Non-cooling water is led by maintenance per MW (0.62), bracketed only by applicants, so metered use at an operating campus is
the most useful single figure. Limits: one climate, two years of weather (so the 1-in-10 peak is close to the hotter year's record).

**Short form (methods pages, briefs).** Electricity: the computers are taken to draw 50 to 80% of their capacity on
average (EPRI 2026 measurements; IEA 2025), plus cooling and power losses by design (LBNL 2024; checked against
Google's and IEA's reported PUE). Power plants: each state's figure comes from its plants' 2024 reports to EIA (with
Macknick et al. 2012 factors where a report is implausible or missing), weighted for power the state imports and updated with 2022 reports and Siddik et al. (2024) on the same basis; Michigan's plants use
up about 1.0 L of water per kWh and draw about 59 L, about 98% returned warmer. People: 20 to 60 plus 0.1 to 0.5 per MW
(JLARC 2024; announced campuses), each using 10 to 30 gallons a day (EPA 2002; Michigan's septic design criteria),
about 10% used up (USGS). Maintenance and cleaning: up to 2,000 gallons a day plus 2 to 20 per MW, bracketed by
applicants' projections, mostly to the sewer. Cooling: heat factors and economizer limits derived from published
component losses and setpoints (Lei and Masanet 2022; DOE FEMP); evaporation from Rutberg et al. (2011) with an
uncertainty that leans low in cold weather (USGS 2013); drift, cycles, loop volume and top-ups from EPA, DOE FEMP,
operators and NIH.

## Oct 30, 2026: 3.2.1 and the Ohio, Virginia and Texas snapshots

3.2.1 fixes a crash in state builds on a machine with no cached EIA-861 (`power.utility_rtos`) and changes no number. The
Ohio, Virginia and Texas snapshots of this date were built from `main` at 888f4d5, which has the fix but is still numbered
3.2.0, so their manifests record 3.2.0. Model version 1.3 in both.

## Oct 30, 2026: electricity from an hourly heat balance (model 1.4)

**Problem.** Through model 1.3, electricity was computing load x utilization x one PUE per cooling design, read from LBNL 2024 Fig. 4.4. Each
value traced to its source, and the source check confirmed them, but the structure was wrong: PUE had no climate term, so Texas had
Michigan's PUE while water came from hourly local weather. Closed loop's 1.15 was the midpoint of two different computer cooling
arrangements, which produced a 3% gap to cooling towers everywhere. The page's explanation compared liquid-cooled closed loop (about 1.10)
with air-cooled towers (about 1.12), not like with like; LBNL's own rows, as read from the figure (about +/-0.02), are towers 1.12 against dry
coolers with assist 1.20 with air-cooled computers, and towers 1.14 against dry coolers 1.10 with liquid-cooled computers. The peak was the top of a
range of annual averages, not a hot-hour estimate. Andrew caught this from the results; checking parameters against sources could not.

**Decision.** Electricity is an hourly output of the cooling model, for every design and state (`physics.hourly_heat_power`, the BMI output
`data_center__electric_power`, `cooling.run_location`, `ensemble.run_ensemble`, `Estimate.electricity`). Scope: the campus's power and the water behind
it; power plant water stays grid-level, a factor per power source. Hourly grid mix and specific plants are out of scope.

**Method.** After Lei and Masanet (2022, Resources, Conservation and Recycling 182:106323; preprint doi:10.21203/rs.3.rs-769999/v1, Eqs. 2-4, Table 3 case 2; the published
paper is closed and the values cite the preprint). The equations are implemented from the paper; their repository
(github.com/nuoaleon/Data-Center-Water-footprint) has no license, so none of its code or fitted chiller curves are used. Per kW of IT:

    q = 1 + (1/UPS - 1) + (1/(1 - dist) - 1) + light
    air = (1 - liquid_share) + liquid_share x liquid_air_share
    crah = fan(q x air / (cp_air x air_rise), crah_pa, fan_eff)                     fan(m, P, e) = m / rho_air x P / e / 1000
    load = (q + crah) / SHR
    air loop supply water = supply_air + air_rise - air_rise / coil_eff             (Lei and Masanet's coil relation)
    liquid loop supply water = liquid_water
    for each loop, carrying its share of the load, with return = supply + water_rise:
        outside = wet x (T_wb + tower_approach + hx_approach) + (1 - wet) x (T_coil + dc_approach)
        free = clip((return - outside) / (return - supply), 0, 1)                   (their waterside economizer)
        chiller = load x (1 - free) / COP
        COP = min(carnot x (T_evap + 273.15) / (T_cond - T_evap), cap)              T_evap = supply - 2
            towers, hybrid: T_cond = T_wb + tower_approach + range + 2, cap 8
            dry, assist:    T_cond = T_coil + 12, cap 5 (an air-cooled chiller's rated COP includes its condenser fans)
        pumps = pump(load x free / (cp_w x water_rise), econ) + pump(load x (1 - free) / (cp_w x water_rise), chilled)
        tower = pump(m, tower) + fan(m / L/G, tower_fan_pa, fan_eff)                m = (load + chiller) x wet / (cp_w x range)
        dry fans = fan(load / (cp_air x air_rise_dc), dc_fan_pa, fan_eff) x clip(flow / design flow, 0.1, 1)^3
    facility power = q + crah + sum of chiller, pumps, tower and dry fans           hourly PUE
    heat rejected = load + sum of chiller                                           drives evaporation, drift and blowdown

wet is 1 for towers, 0 for dry and assist, and the existing dry-bulb ramp for hybrid. T_coil is the dry-bulb, lowered by pad effectiveness x wet-bulb depression
above the switch point for assist. Reported: annual PUE; average MW (at the run's utilization); PUE and MW in the 1-in-10-year hottest hour (90th percentile of each
year's hottest hour), with every computer at capacity.

**Departures from Lei and Masanet, stated.** Air handler fan heat is counted in the load, so the energy balance closes (their Eq. 2 leaves it out). Dry coolers and
liquid cooling are added; their cases do not have them. The chiller is a Carnot fraction, not their Gaussian process regression. Humidification is not modeled, as before.

**Water changes too.** Lei and Masanet's point is that PUE and WUE must come from the same heat balance, so evaporation now follows the heat rejected above, which
replaces the heat factor `hf_econ`, `hf_chiller` and the wet-bulb limits `wb_econ`, `wb_chiller` (removed; the lake-source range keeps 1.03-1.25 as a stated estimate).

**Inputs and where they stand.**
- Lei and Masanet Table 3, case 2 (large-scale): UPS 90-99%, distribution 0-2%, lighting 0-0.2%, SHR 95-99%, supply air 27-35 C, air rise 13.9-19.4 C, coil effectiveness 0.7-0.9, water rise 5-10 C,
  CRAH 300-700 Pa, fan efficiency 65-90%, tower fan 100-400 Pa, L/G 0.2-4, tower approach 2.8-6.7 C, heat exchanger approach 1.7-2.8 C, pumps 114.9-172.4 and 166.9-250.4 kPa at 60-80%.
  Their CRAH pressure was also read as 300-1000 for case 1; case 2 is used because cooling towers are its design.
- Chillers: water-cooled 0.62-0.78 of Carnot. Code minimums for large plant (WAC 51-11C-403323, a stated replica of ASHRAE 90.1 Table 6.8.1-3, edition not stated): 0.560 kW/ton is COP 6.28; with
  rating conditions 44 F, 85 F (reported in summaries, AHRI 550/590 not read) and a 9.3 F rise, eta is 0.72; 0.585 kW/ton gives 0.69. C403.3.2.4's part-load adjustment gives 0.67-0.73. EnergyPlus Chillers.idf, 39 chillers of 2,100 kW or more:
  median 0.66, 5-95% 0.53-0.75. Range: 0.70 +/-11% (Lei and Masanet's COP error). Air-cooled 0.45-0.55: EER 10.1 is COP 2.96, eta 0.45 at condensing 47 C; the top is an assumption. The offsets (2 K, 2 K, 12 K) and the caps are assumptions [A], and eta is fitted with them: at 16.7 K, 90.1's air-cooled condenser rating, the floor is 0.50.
- Dry coolers [A]: no standard or peer-reviewed design values were found; selection data are proprietary. Approach 5-10 K (ThermoKey catalogue point 10 K; a vendor preprint, Mokkapati and Das 2026, 2.8-5.3 K at El Paso, not adopted), pressure 100-250 Pa, fan efficiency by analogy, cube law (the preprint: roughly cubic, flattening at deep part load). The prototype's specific fan power, 7.4-36.8 W per kW, compares with 90.1's air-cooled condenser minimum of about 14.5 W/kW at a wider difference, an analog. That preprint also implies a peak gap of about 3 MW per 10 MW between dry and adiabatic, far above this model; unverified and not adopted.
- Liquid: facility water 32-45 C, ASHRAE TC 9.9 classes W32-W45 (LBNL 2024 Table 4.3: W45; classes are upper limits). Air share 10-30%: HPE GB200 NVL72 12.9% (summary only), Schneider WP210 20% (an illustration), ASME InterPACK2022 25.1-38.6% (through a Vertiv blog; the paper was not read). Liquid share 0-1 [A]: no fleet figure is published. Air-side heat goes to a separate, cooler loop, since 45 C water cannot supply 27-35 C air (found in review of the first prototype).

**Checks.** Cooling towers, air-cooled computers, 300 draws, station weather 2005-2024, 5-95% against Lei and Masanet's case 2 for the climate zone: Houston 1.107-1.246 (1.099-1.250), McAllen 1.113-1.263 (same zone), Fort Worth 1.098-1.230 (1.087-1.215), Lubbock 1.088-1.202 (1.080-1.192), Richmond 1.096-1.213 (1.084-1.202), Dulles 1.093-1.208, Columbus 1.089-1.203 (1.083-1.196), Cleveland 1.089-1.201, Las Vegas 1.086-1.197, Phoenix 1.093-1.209 (2B, 1.084-1.201). About 0.01 high at the low end. Closed loop over towers, air-cooled computers, medians: Cleveland +1.2%, Columbus +1.7%, Dulles +1.9%, Richmond +2.4%, Lubbock +4.0%, Houston +4.3%, Fort Worth +5.1%, McAllen +5.9%, Las Vegas +7.2%, Phoenix +8.4%; Han et al. (arXiv 2603.02705, a preprint) report 6.4-10.2% in Nevada for one operator; Karimi et al. (2022, RCR 181:106194, abstract only) nearly 13% at two Phoenix colocation sites, different facilities. LBNL (read by eye): liquid dry about 1.09-1.10, this model 1.10-1.15; liquid towers about 1.13-1.14, this model about 1.11, low, unexplained. No peer-reviewed comparison of liquid-cooled dry against towers by climate was found, so closed loop below towers in cool climates is a modeled result.

**Results, state averages.** Median annual PUE, closed loop / towers, liquid share sampled: Michigan 1.122 / 1.129, Ohio 1.131 / 1.130, Virginia 1.137 / 1.132, Texas 1.172 / 1.141. Hottest hour: 1.289 / 1.201, 1.299 / 1.211, 1.306 / 1.204, 1.331 / 1.209. West Michigan, 300 MW, model 1.3 to 1.4, medians: average MW closed loop 222 to 216, assist 222 to 214, hybrid 220 to 213, towers 216 to 217; peak MW 372 to 387, 372 to 373, 351 to 361, 348 to 360. Water used up: towers -0.4%, hybrid +8.3%, assist -0.7%.

**Open.** The liquid share is the largest structural assumption, and a user-settable share is not on the pages. Part-load behavior is proportional to the IT load. Lake-source cooling is not in the hourly model; the towers stand in. The Michigan ERA5 and station weather difference still applies. Sensitivity (`sensitivity/`, 38 parameters, West Michigan): UPS efficiency leads annual PUE in every design (ST 0.65-0.73), so its 90-99% range is the first to narrow; the liquid share leads the hottest hour (0.41-0.55) and is unsourced; dry cooler assumptions matter little (at most 0.07). Water hardly responds to the heat balance terms.

## Oct 30, 2026: one rounding rule on the pages

Withdrawn to two significant figures, evaporated to the same place, wastewater the difference, in `scenario.cooling_estimate` and `WQ.split`, so what is shown adds up (before, the middle values were rounded separately and a tile could read 74,000 beside a table's 73,600). The ranges stay the model's own. `Estimate` middle values carry this rounding.

## Oct 30, 2026: a typical golf course in every state

One basis: the median facility, gallons a day averaged over the year, reported data where the state reports it. `waterledger_data.wateruse.GOLF`.
- Michigan: EGLE 2025, median of 453 facilities, 43,500 (name-matched; unchanged).
- Ohio: ODNR Water Withdrawal Facility Registration, facilities with use type Golf Course and more than 0 reported: medians 32,500 (2022, n=280), 33,300 (2023, n=272), 43,100 (2024, n=265); the middle, 33,300, is used because 2024 stands well above the other two. Only facilities able to withdraw 100,000 gal/day register, so it may run high. The 2024 sum, 15.4 Mgal/d, is close to USGS's 16.2.
- Virginia: GCSAA (2022), Golf Course Environmental Profile, Phase III, Vol. I (2020 data; Shaddox and Unruh), Table 2, p. 7: Transition region, median 38.5 acre-feet a facility, 34,400 gal/day at 325,851 gallons an acre-foot. DEQ's "commercial" (13.41 Mgal/d in 2024) includes resorts and universities, so golf is not separable; facility rows are only in its dashboard.
- Texas: GCSAA by region, Southeast 111.1 acre-feet (99,200 gal/day) and Southwest 375.7 (335,400). One state number would hide a 3.4-fold difference. The report's Figure 1 (p. 3) is a map with no county list, so climate divisions are assigned by reading it [A]: High Plains, Low Rolling Plains, Trans-Pecos, Edwards Plateau, Southern and Lower Valley to the Southwest (Phase II puts San Antonio there), the rest to the Southeast. Cabrera et al. (2013), about 364 acre-feet a course (325,000 gal/day), is potential use, acres x rate, not metered, and is near the Southwest figure.
- Rejected: USGS 2015 county golf (IG): no course counts, and zero in every Texas county.
- Check: GCSAA's North Central figure (40.5 acre-feet, 36,200 gal/day) is within about 20% of the reported Michigan and Ohio medians, which supports it where no reports exist. Limits: a survey, and 9-hole facilities pull medians down.

## Oct 30, 2026: starting cooling design

**Question.** Should hot states start at hybrid or cooling towers? **Finding.** Heat does not predict the stated design. Named projects with a stated design, nearly all developer claims and not a sample (counts are floors; the state lists are unreviewed): Michigan 5 closed or air, 1 mixed; Texas 5 closed or air (Crusoe Abilene, Google Wilbarger, Skybox read; Vantage Frontier and Google Panhandle from summaries), 1 towers (Meta El Paso); Ohio 3-4, weak, 0 water-based; Virginia 0-1 closed, 1 water (Google Botetourt). ICPRB: about 40% of Potomac facilities air-only, many hybrid. JLARC 598 gives no design counts. Evaporative designs tend to stay silent, so closed loop is probably overcounted. LBNL 2024 Fig. 4.2 (chart reading) models the 2023 hyperscale fleet as about 85% airside economizer with adiabatic cooling: the fleet looks hybrid while announcements look closed, though that is national and older than the proposals.
**Decision.** Closed loop as the start everywhere, stated as an assumption with each state's own note, and every design shown beside the first number ("Water Used by Cooling Design"), so no reader leaves with only the lowest figure. Alternatives: hybrid everywhere, the case from LBNL's fleet; by climate, not supported.

## Oct 30, 2026: road salt by climate, and what is not counted

**Road salt.** The 20-60 events a winter were Michigan's assumption applied everywhere, so Texas pages showed tons of salt. Outside Michigan, events are now each climate division's median winter days with precipitation at 1 C or below (NOAA ISD-Lite, 2005-2024) x 0.6, +/-50%; below 2 days a winter there is no salt, and the row is left off. The 0.6 brings Grand Rapids (72 days) and Detroit (59) to Michigan's assumed 40, so it is a calibration to an assumption [A], not a measurement of salting. Examples, middle events: Cleveland 37, Columbus 27, Dulles 11, Richmond 5, Lubbock 5, Fort Worth 2, Houston and McAllen none. Michigan keeps 20-60. This is computed in Northline's `engine/products/state_data.py` for now and should move to the packages.

**Not counted.** The calculator covers the campus's water, electricity and runoff on the site. It does not count new water or sewer connections, power lines, access roads or other construction beyond the site. Stated on the calculators and methods pages.

## Oct 30, 2026: starting assumptions by state

Pages no longer use another state's evidence. Each state's data carries its starting cooling design and a note (`state.defaults.cool`, `cool_note`). Only Michigan's proposals have been reviewed for cooling design; the others state what was found and that closed loop is assumed. The runoff standard is described as a typical post-construction standard on other states' pages; the source list still cites the Michigan permit it comes from.

## Open

- UPS efficiency is the first input to tighten: it leads annual PUE (ST 0.65-0.73). Kept at 90-99% (Lei and Masanet Table 3, LBNL 2024 Table 4.3) on Oct 30, 2026, since nothing independent and measured for large campuses was found. ENERGY STAR's guidance page says new efficient units are generally 92-95% and older ones can be under 90% (an older page); FEMP's purchasing example runs 97.3-99.3% (only part of the table was read, and the size may be smaller than a campus); vendors and trade press give about 97% for the best double conversion and 98-99% in eco mode. A low end of 92% would lower average electricity about 0.5%, and 95-99% about 2.5%, without changing how the designs compare. A question for an electrical or data center expert.
- Model 1.4 is on the branch `hourly-electricity`, not released. Release: merge, tag, publish the four snapshots (`build-state`), rebuild page data from them, regenerate the methods pages and briefs.
- Sensitivity analysis: repeat with a hotter climate's weather (West Michigan only so far); the repo has no other hourly weather.
- Check Lei and Masanet's published Table 3 (Resources, Conservation and Recycling 182: 106323) against the preprint
  used here, with library access; metered water at an adiabatic site.
- Landscape irrigation as an optional, climate-specific term.
- Station distance: how far places are from their division's station, and how much a nearer station changes the
  estimates ([station-distance-check.md](station-distance-check.md), in progress).
- NOAA climate division names in the data.
- Virginia's withdrawals by use type (published only in DEQ's dashboard; a bulk export to request).
- The share of homes a utility serves, shown for Michigan, needs a national source.
- Michigan's move to the shared format (design 0003, decision 8). Done for the package: Michigan's snapshot is in the shared
  format and `waterledger build-state MI` runs Michigan's own build (`waterledger build mi` stays). Still open: the pages
  reading the shared files, and with that Michigan's home electricity figure.
- Byte-identical snapshot rebuilds.
