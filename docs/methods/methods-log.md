# Methods log

A dated record of method decisions: what was decided, why, what else was considered, and what is still open. It is the
long form. The short forms are the two-page briefs (`docs/methods/<st>.pdf`) and the methods pages on waterledger.org
(`/methods/`, `/methods/<st>/`, Michigan's `/mi/methods.html`), and they are kept in step with this log.

Layer-by-layer notes for the national tier (places, water supply, wastewater, receiving waters, climate, energy) are in
[national-tier-notes.md](national-tier-notes.md); county water use sources are in [water-use-sources.md](water-use-sources.md).
This log covers decisions that cut across layers, and points there for detail.

## Oct 30, 2026: Michigan builds on GitHub like the other states

`waterledger build-state MI` now downloads Michigan's sources and builds from an empty cache, so its snapshot no longer waits for
a site deploy. EGLE's water-use file, which EGLE will not serve to scripts, ships in the package (`states/mi/inputs/`) with facility names
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

## Oct 31, 2026: the packages as the standard; storms by curve number

Decision (Andrew): the packages are the standard, and waterledger.org is built on them. Where the two disagree, the package wins.

- **Rounding.** Estimates and context carry full values. A middle value rounded to two significant figures sat beside unrounded p10 and p90, so a Gaines
  hybrid peak day read 1.6 MGD against the model's 1.576. On the middle estimate, returned is withdrawn less consumed.
- **Comparisons.** `est.comparisons` holds the water system comparison the site made: water as homes at 300 gallons a day (EPA WaterSense) as a percent of
  the connections of the largest system mapped in the place, average and peak day. It is not a percent of the system's water use: connections include
  businesses, and the system's own gallons are not in the public data.
- **Single storms.** One storm's runoff uses curve numbers (NRCS TR-55; `runoff.storm_mg`; hydrologic soil group B [estimate]), with pavement and lawn computed
  separately. The Simple Method (Schueler 1987) stays for the year. The page had scaled a Simple Method inch in proportion to the storm. On 200 acres half
  impervious: 1 inch 2.1 MG (was 2.7); 2.57 inches 7.2 MG (was 7.0). Runoff rises faster than rain, which proportional scaling cannot show.
- **A place's own sewer plant: one rule.** Michigan sorted a name-matched plant first at any distance; the national tier used it only as a flag, because the survey's
  city is a mailing city. Measured in the four states, name matches within 10 km are nearly always right (median 1.5-2.8 km). Beyond it many are coincidence (Sandusky County and
  Sandusky city's plant, 37 km; Butler Township, Knox County, 32 km; Ohio has 39 Jackson Townships). So [A]: a plant with the place's name comes first if it is within 10 km, otherwise the
  nearest plant, in every state. Andrew's judgment, Oct 31: pick reality and reason; that Michigan's rule came first gives it no standing. Known cost: a city whose own plant is truly
  far (Mesquite, Texas, 27 km) or far only on the map (Brown City, Michigan, 30 km) gets its nearest plant instead.
- **Local weather.** `site.estimate(weather="local")` runs the model at the place's ERA5 cell. For Gaines, 14 km from the West Michigan point, hybrid's peak-day median is
  1.50 MGD against 1.58, small against the parameter range of 1.16 to 2.09. It is reanalysis, not on-site weather.
- **Residential customers.** Michigan 4,538,056 (EIA-861 2025), replacing 4,516,367 (2024) that the pages carried alongside a 2025 kWh figure.

## Open

- UPS efficiency is the first input to tighten: it leads annual PUE (ST 0.65-0.73). Kept at 90-99% (Lei and Masanet Table 3, LBNL 2024 Table 4.3) on Oct 30, 2026, since nothing independent and measured for large campuses was found. ENERGY STAR's guidance page says new efficient units are generally 92-95% and older ones can be under 90% (an older page); FEMP's purchasing example runs 97.3-99.3% (only part of the table was read, and the size may be smaller than a campus); vendors and trade press give about 97% for the best double conversion and 98-99% in eco mode. A low end of 92% would lower average electricity about 0.5%, and 95-99% about 2.5%, without changing how the designs compare. A question for an electrical or data center expert.
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
- Sewer plant coordinates: some sit far from the place they are named for (Brown City, Vermontville and Cedar Springs, Michigan, 20-30 km). Check against the permits.

## Oct 31, 2026: independent cities in the national tier's rainfall and storms

Found while checking whether rate limiting had lost counties in the Oct 31 builds. It had not, but Virginia's published
snapshot had rainfall for 95 of 133 county equivalents. The 38 missing are its independent cities, so 38 of its 322
places had no rainfall or design storms, Richmond and Virginia Beach among them. `national.climate.counties` kept only
rows at county level, and `census.places` lists independent cities as places, so they were never asked for. The statewide
check passed because it did not look at rainfall or storms. NOAA does publish them: Climate at a Glance has Richmond as
VA-760, and Atlas 14 answers at the city's point (24-hour 2-year 3.35 in, 100-year 8.43 in).

Decision: `climate_areas` asks for counties plus any place whose county code has no county row, at the place's own point.
Cooling stations stay on `counties`, because a division's station is chosen from the center of its counties and moving
it would change cooling results for a reason unrelated to this error. No water use estimate changes; rainfall and storm
figures appear where they were blank. The statewide check now requires 99% of places to have each, the standard of its
other layers. A state outside Atlas 14 will fail that check until it has a storm source, which is the intended result.

A rate-limited county used to be skipped silently (`except Exception: continue`). It now waits, up to 6 tries, and fails
the build if still refused. A county NOAA does not publish is still left out, and the check reports the shortfall.

## Oct 31, 2026: homes, golf courses, plant water and evaporated share in the package; Lexington's rainfall

These were computed on the website, with no equivalent in the packages. They move to `waterledger.comparisons`, return on
`est.equivalents` and `est.power_plants` at full value, and the pages mirror them with a parity check in all four states.

Package and page differ on what comparisons start from. The package works from full values, as its rule says. The pages show water rounded to two significant figures
and work out homes, golf courses, shares and levels from those shown figures, so a reader can reproduce each result from the numbers on the page. This was Andrew's decision (Oct 31,
2026), after full values were tried on the pages and compared. The cost is rounding twice. In Southeast Michigan weather at 1,000 MW of hybrid cooling, 0.2818 and 0.2096 MGD round to 0.28 and
0.21, which read as 8 of every 10 gallons evaporating, where the full values give 74%, or 7 of 10. Over every weather region and 7 sizes in the four states, with each cooling design (952
cases), the page's homes figure differs from one made from full values in 30% of average-day and 27% of peak-day cases, by at most a few units in the second significant figure, and golf
courses in 9%. For the evaporated share, closed loop's percent differs in 136 of 238 cases, by up to 2 points, and "of every 10 gallons" for the other designs in 51 of 714, by one. So `est.equivalents`
and the page can read differently by that much. The parity check applies the page's rounding rule to the package's values, then the package's functions, and compares with the page.

Power plant factors stay in whole gallons per MWh. The rule that the package does not round concerns results. These are
factors quoted as written (Michigan's mix: 268, range 197 to 364), and at most 0.5 gallon in about 178 (0.3%), far inside
their ranges. The two conversions in use (3.78541 for Michigan, 3.785411784 elsewhere) are now one, the exact value; no
rounded factor changes.

Lake-source comparisons count what the lake loses, not what runs through, since nearly all of it returns. The pages did
this; the private screening text counted the water run through, and now follows the package.

Lexington. NOAA Climate at a Glance answers 404 for VA-678. Lexington lies inside Rockbridge County, whose 1991-2020 mean is
44.79 inches; neighboring Buena Vista city reads 44.89. It took Virginia's median before. The alternatives were the nearest
city with a record, or the median. A surrounding county is measured at the same scale and covers the land around the city, while
a median stands for the whole state and another city's record for somewhere else. The surrounding county is the one covering most of a 1 km ring
around the city, in CONUS Albers. `Climate.rain_from` and the snapshot's `rain_from` name the county, so the substitution is visible. Of the
independent cities in the published states and Baltimore, St. Louis and Carson City, only Lexington lacks a record.

A county with no record now stops the build; the earlier code skipped it, and any other failure, without saying.

## Oct 31, 2026: the other comparisons and the before-and-after table in the package

`waterledger.comparisons` now holds the campus against the county's water, the sewer plant and its spare room, the utilities and the state,
and the place's before-and-after as numbers. Words stay with each display; the private engine and the page word the same numbers,
and a check compares both in all four states.

As with homes, the package's shares use full values and the pages' use the rounded water they show (the decision above): a county percent to one decimal differs between them in 5,005 of 8,344 cases checked, and a sewer percent of flow in 6,730 of 9,520. A utility reporting zero sales (Southwestern Electric Coop in Texas, Bayfield Electric in Michigan) was treated as a load of zero, so the page divided by it; it now counts
like one reporting nothing. The county figure falls back on all reported withdrawals where a county's table has no public water figure, as the
pages did. The before-and-after table's water row still uses only the public figure, because a label saying public water would misdescribe the total.

Land defaults for `est.before_after` follow the page: cities 50 acres already built, others 200 acres of farmland [A]. Snapshots now carry road salt events by
division, so the national tier does not need NOAA's station files at estimate time.

## Oct 31, 2026: design totals, closed loop's trade and contract size in the package

`site.by_design()` compares a campus across cooling designs, on one power option, as `comparisons.compare_designs`: water at the campus and at power plants, which evaporates least, the thirstiest power option other than wind and solar and the state's starting mix, and what closed loop trades against cooling towers. The pages' on-site water is rounded for display, and the package's is not; which design evaporates least comes out the same either way in all 1,610 region, size and power cases checked, so the pages use the shared comparison for that answer. The simple page compares closed loop, hybrid and towers, and the detailed page adds air-assisted in its table; that choice of rows is the page's, and is left alone. `it_mw_from_contract` is contract power over the design's hottest-hour PUE, and the page rounds it to 10 MW.

## Oct 31, 2026: starting power, the impairment filter and well summaries in the package

`comparisons.default_power` and `offered_power` are the page's rules for a site's power option: a state with its own mix starts on it and keeps grid averages for comparison only; otherwise a site starts on the grid region of the utility serving most of the place. All four published states have their own mix, so this changes nothing there today. `runoff.listed` is the filter for impairments a site's runoff can add to; it leaves out bacteria and mercury in fish, as the pages and the engine did with separate lists. `comparisons.wells_summary` says which aquifer most household wells draw from, with too few under 10 wells [A]. Michigan is the only state with well records. No number moves.

## Oct 31, 2026: public levels and verdicts in the package

`waterledger.levels` holds the bands behind what waterledger.org shows a reader (a water system's 2% and 10%, a plant's spare room at 10% and 50%, a small system, a plant near its design size, when a peak is worth saying, when sediment is "about as much") and the verdict comparing a reported figure with an estimate. These are this project's readings, marked [A]; only the withdrawal and Compact lines come from rules. They are published in `context.levels` so the pages read them. Northline's paid review keeps its own ratings and text.

`est.levels` uses full values and the pages rate the figures they show, so a figure rounded across a line can read differently: 9 of 952 well withdrawal levels and 94 of 9,520 spare-room levels checked, and none of the Compact levels or the verdicts on the 6 proposals with a reported figure. Wording stays with each page: the simple and detailed pages say "with the state" and "with EGLE" for the same line, which is left alone as a choice of words. The single-storm method was settled earlier (curve numbers, `runoff.storm_mg`); the private review's yearly and first-inch figures remain its own.

## Oct 31, 2026: a stable order for utilities tied on customers

`energy.ranked` orders a place's utilities by EIA customers in the state. Utilities reporting the same number, usually delivery-only ones reporting none, kept whatever order the territory data arrived in, and two builds a day apart swapped them at 158 places in Texas and one in Virginia, with the same utilities and shares. Ties now go to the larger share of the place, then the name. Share is the better first tie-break because it is the only other measure of how much of the place a utility covers, though HIFLD's whole-county territories overstate it; the name only makes the order repeatable.


## Nov 1, 2026: model 1.5, mass and energy balances

Working one hybrid hour by hand from the written equations matched the code, and showed the code's own books did not always balance. Andrew asked that the calculations follow a mass and energy balance, so each flow of water, heat and dissolved solids was audited, then held to closure by tests (`tests/test_balances.py`), for every design, at 100 parameter draws, from -25 to 40 C.

**Energy.** Before, heat rejected was load / SHR + chillers and facility power also counted pumps and fans, so the two could not be reconciled. Now, per kW of IT:

    facility power + outside air heat = heat rejected + heat rejection fans          whose heat goes straight to the exhaust air
    heat rejected = q + air handler fans + outside air heat + chillers + pumps       through the water or coil
    air loop load = q x air + air handler fans + outside air, sensible; liquid loop load = q x (1 - air); a third loop at 9 C carries the latent part [A]
    chiller = load x (1 - free) x (wet / COP_water + (1 - wet) / COP_air)
    tower flow m: m x cp x range = wet x (load + chiller + pumps + m x dP / eff)
    L/G <= (h_sat(hot water) - h_sat(wet-bulb)) / (cp x range), hot water = max(wet-bulb + approach + range, return - heat exchanger approach)

A balance does not by itself say all electricity becomes heat. Physics does: a data center stores almost nothing, so its electricity ends up as heat, and the balance asks where every kW comes from and goes. Electricity is also not the only energy crossing the boundary, which is why outside air is in the equation.

**Outside air, in place of the sensible heat ratio.** Lei and Masanet's Eq. 2 divides the load by a sensible heat ratio, 0.95-0.99, which adds 1-5% to the heat as the latent load of condensing moisture. Latent heat is real where moisture enters the building, but the ratio had no source for it. At 300 MW and 65% utilization, a ratio of 0.97 means about 56,000 gallons of condensate a day, every day, against about 79,000 for a hybrid's whole average-day water. Matching 0.97 on average would take about 34,000 cfm of outside air per MW in West Michigan, 7,200 in Austin and 4,800 in Houston, 16 to 110 times the 300 cfm/MW below. The air loop's water is also 18.7 C or warmer in every draw, above the 15 C indoor dew point limit, so those coils run dry.

The ratio is replaced by the air's own balance. Flow: 100-1,500 cfm per MW of IT capacity [A]. ASHRAE 62.1's area rate for computer rooms, 0.06 cfm/ft2 (2007 table, quoted secondhand at leeduser.buildinggreen.com/forum/data-center-outside-air-requirement), at about 5,000 ft2 per MW [A] gives 300; the ends are a bracket; no published flow for large campuses was found. The air leaves at the supply air temperature with humidity held between dew points of -9 and 15 C (ASHRAE TC 9.9's recommended range as secondary sources give it, not read directly: hvacengineering.ca/guides/ashrae-tc-9-9-thermal-guidelines-for-data-centers/). Above the limit a coil at 9 C [A] condenses the extra, and it goes back with the wastewater. Below it, humidifiers make up a share sampled from none to all [A], since some facilities no longer humidify (hvac.best/ashrae-tc-9-9/); they are taken as adiabatic [A], and their water is consumed. Heat = air flow x (enthalpy outside - enthalpy leaving). The sensible part is usually larger than the latent part and usually cools: about -1,050 kW against +57 kW at 300 MW and 300 cfm/MW in West Michigan, on a 30 C indoor assumption.

Water therefore closes as withdrawn + condensate = consumed + returned. Condensate comes from the air, not a water system. With reuse, it offsets water taken. Direct outside-air designs would use far more air and are not modeled. Moisture comes from the hour's relative humidity, passed through as `rh`: worked back from Stull's wet-bulb it is off by several times in cold, dry air, where humidifiers run.

Heat through walls and roofs is not counted. Roughly, 5,000 ft2 of roof per MW at U = 0.3 W/m2K and a 40 K sol-air difference [A] is about 0.6% of IT load in the sun, and less otherwise, and it runs the other way in winter.

The ratio's slot in the random stream is still drawn, so the other parameters keep their draws. Outside air has its own stream. Pump heat is added: pump work ends up in the water (about 2% of IT load at a tower in full use). The air handler fans' heat all goes to the air loop. CP_WATER is 4.1868 kJ/kg/K, the 1 BTU/lb/F the water terms use, so tower flow is one quantity in both equations.

The L/G cap comes from the air side of the tower's energy balance. Lei and Masanet's Table 3 gives L/G 0.2-4, but at hot, humid hours the air could not carry the tower's heat at the top of that range, leaving hotter than saturated at the hot water. The cap sets air flow where the sampled ratio is impossible. Only fan power changes. In cool weather the tower's water is held near the loop's return, not at the wet-bulb plus approach, so the cap does not bind there.

**Hybrid chillers.** They were always water-cooled, with the water's condenser temperature and COP, even at a wet share of zero, where the model evaporates nothing. About 1,340 hours a year in West Michigan (central parameters) ran a chiller that way. They now split by wet share. At a wet share of 0 a hybrid's heat and chiller are those of a dry design; at 1, those of towers.

**Water.** Three changes:

    drift = heat x wet / (8.34 x range) x drift share                               was all the heat in any hour with wet > 0
    blowdown + drift = evaporation / (cycles - 1)                                   solids in = solids out; was blowdown = evaporation / (cycles - 1), with drift on top

DOE FEMP's blowdown relation neglects drift. With it, makeup x solids = (blowdown + drift) x cycles x solids, so drift comes off blowdown, and withdrawn is evaporation x cycles / (cycles - 1) plus top-ups. Assist pads are unchanged: their evaporation already follows the air's energy balance and their bleed is a share of it.

**Lake-source.** Heat factor 1.05-1.17 (was 1.03-1.25, an estimate carried from model 1.3). It is IT, losses, lighting, air handler fans and pumps from the POWER ranges (5th to 95th percentile about 1.06-1.16), with no chillers or heat rejection fans because the lake water is colder than the loops [A]. All the electricity leaves in the water, so PUE equals the heat factor, and the estimates now report that instead of the region's cooling towers. Withdrawn equals returned at the pipe; the forced evaporation happens on the lake afterward, so the control volume for that balance is the lake. A lake-source campus's staff water comes from a water system, not the lake, and is not in the lake's withdrawal.

**Power plants.** Plant water factors are plant water over net generation (`power_water/README.md`). The plants generate what the campus uses plus what the lines lose, so water at power plants is now electricity / (1 - 0.05) x factor. EIA FAQ 105: U.S. T&D losses "averaged about 5%", 2018-2022. A campus on the transmission system may lose less [A]; the national figure is used because no campus-level one is published. A campus's share of a utility's load stays on sales, which are delivered electricity.

**Smaller.** Farmland sediment replaced the whole site's runoff load with field erosion, dropping the paved 2%. It now keeps that part. Reuse and lake annual totals used 365 days a year and the rest 365.25.

**Checked, nothing to change.** Staff water closes. Assist evaporation is the air-side energy balance. Lake flow x rho x cp x rise = heat. Runoff is a part of the rain, and the unit constants (0.226, 27,154 gal/ac-in, 8.34) agree. Chloride is 35.45/58.44 of salt. Blowdown solids are makeup x cycles.

**Measured** (per 100 MW of IT, 200 runs, 30 years of ERA5, p50 of cooling water, staff water excluded, 1.4 to 1.5):

| | West Michigan | Austin, TX | Houston, TX |
|---|---|---|---|
| Hybrid withdrawn, average day | 0.0240 to 0.0238 (-0.5%) | 0.1655 to 0.1643 (-0.8%) | 0.1500 to 0.1476 (-1.6%) |
| Hybrid withdrawn, peak day | 0.5120 to 0.5068 (-1.0%) | 0.7562 to 0.7436 (-1.7%) | 0.6577 to 0.6522 (-0.8%) |
| Hybrid annual PUE | 1.1148 to 1.1220 (+0.6%) | 1.1412 to 1.1498 (+0.7%) | 1.1438 to 1.1565 (+1.1%) |
| Towers withdrawn, average day | 0.6466 to 0.6275 (-3.0%) | 0.7146 to 0.6974 (-2.4%) | 0.7167 to 0.7034 (-1.9%) |
| Towers returned, average day | 0.1205 to 0.1119 (-7.1%) | 0.1316 to 0.1253 (-4.8%) | 0.1324 to 0.1273 (-3.9%) |
| Assist withdrawn, peak day | 0.3594 to 0.3525 (-1.9%) | 0.6989 to 0.6832 (-2.2%) | 0.5830 to 0.5752 (-1.3%) |
| Closed loop withdrawn, average day | 0.00004 to 0.00008 | 0.00004 to 0.00005 | 0.00004 to 0.00004 |
| Closed loop withdrawn, peak day | 0.00004 to 0.00057 | 0.00004 to 0.00036 | 0.00004 to 0.00026 |
| Condensate, average day | 0.00045 | 0.0022 | 0.0033 |
| Condensate, peak day | 0.0079 | 0.0085 | 0.0101 |

Staff and maintenance water is added to these, about 0.007 MGD at 300 MW, so closed loop's full estimate moves far less than these ratios. Southeast Michigan follows West Michigan. Midland, in dry West Texas, has condensate of 0.00037 on average, closer to Michigan than to Houston.

Water at power plants rises 5.3% from line losses, on top of any change in electricity.

**Still open, not balance errors.** Outside air's flow is a bracket until a campus figure is found. Peak-hour electricity reads the outside air per kW at average utilization. The peak-day water is at the run's average utilization while the hottest-hour electricity is at full capacity, so the two peaks describe different conditions. Farmland phosphorus adds soil-attached phosphorus to a runoff concentration that may already include some, which could double count. Reuse takes all blowdown back, with no brine stream for the dissolved solids. The ranges of an estimate add the model's and staff water's ends together, so p10 and p90 of withdrawn, consumed and returned do not add up, though each run does.

## Nov 1, 2026: model 1.6, from an independent review of model 1.5

An independent read of the 1.5 code found errors the balance tests could not see, because they close either way. Andrew approved all the fixes. His rule for the judgment calls: "when in doubt reasonable, accurate, reality based."

**The middle estimate.** Returned's middle was withdrawn p50 + condensate p50 - consumed p50. Medians do not add, and blowdown's skew from the cycles range makes that remainder 13% (towers, assist) to 23% (hybrid) above returned's own median. Withdrawn and returned now stay at their medians, and consumed is the remainder, `max(0, w + condensate - r)`, so the books close on the middle estimate. Consumed's middle now sits up to about 3% above its own median for towers. Its range is the model's own. Andrew chose which flow takes the remainder.

**Tower fans.** They ran at design L/G in every hour with evaporation, which overstated towers against closed loop. Now:

    design water = load / (cp x range); design potential = h_sat(25.6 C + approach + range) - h_sat(25.6 C)
    design air = design water / min(L/G, design potential / (cp x range))
    air share = (tower water / design water) x design potential / (h_sat(hot water) - h_sat(wet-bulb))
    tower fan = fan power at design air x clip(air share, 0.1, 1)^3 x (wet > 0)

The design point is the 78 F wet-bulb of the standard tower rating, 95/85/78 F [A]; a site's own differs by a few degrees. The air needed goes with the water's heat over Merkel's driving potential, saturated air at the hot water less saturated air at the wet-bulb, holding the design point's effectiveness. Fans follow the affinity law with a 10% floor, like the dry cooler fans. The hot water stays near the loop's return in cool weather, not at the wet-bulb. The review's trial, saturated air at the hot water, was an upper bound on the saving; this one takes the same air flow form with the effectiveness kept. Peak-hour power hardly moves, since a tower's fans are near design then.

**Losses to room air.** `q x (1 - air)` put a share of UPS, distribution and lighting losses on the liquid loop. That heat reaches the room's air whatever cools the computers: room = q - (1 - air), air load = room + air handler fans + outside air, liquid load = 1 - air. In rare bitter hours outside air can cool more than the air loop carries, and the rest comes off the liquid loop. Energy closes as before.

**Lake-source homes on the peak day** came from withdrawn, the water passing through. They now come from what the lake loses, like the average day.

**Septic.** Michigan's rules (Part 22: R 323.2210, 2211, 2216) are for sanitary sewage, and from model 1.5 the rule received condensate. That moved the rule's wording at 250, 400 and 500 MW for clean water that would not reasonably go to a drainfield. A septic estimate's flow now leaves it out, and it is assumed to go to a site drain or stormwater [A]. It stays in returned, so the books close. Closed loop to septic, Michigan's 8 regions, gallons a day as the page rounds them:

| MW | 1.4 | 1.5 | 1.6 |
|---|---|---|---|
| 25 | 2,000 | 2,200 | 2,000 |
| 50 | 2,400 | 2,500-2,700 | 2,400-2,500 |
| 100 | 3,200 | 3,500-3,800 | 3,200-3,300 |
| 200 | 4,700 | 5,300-5,900 | 4,700-4,800 |
| 250 | 5,500 | 6,200-6,900 | 5,500-5,600 |
| 300 | 6,200 | 7,100-7,900 | 6,200-6,300 |
| 400 | 7,800 | 8,900-10,000 | 7,700-7,800 |
| 500 | 9,000 | 11,000-13,000 | 9,000-10,000 |
| 600 | 11,000 | 13,000-14,000 | 10,000-11,000 |
| 1,000 | 17,000 | 20,000-24,000 | 17,000-18,000 |
| 1,500 | 25,000 | 29,000-33,000 | 25,000-26,000 |

The rule thresholds, 6,000 and 10,000 gallons a day, fall where they did in 1.4, except that one region reaches the permit at 500 MW after rounding.

**Upper case on the peak day.** The peak day is at each run's average utilization, 50-80% [A]. Hottest-hour electricity is at full capacity, so the two peaks describe different conditions. Andrew kept average utilization as the main number. The upper case, every computer at capacity all day, is `est.water.withdrawn_peak_full_capacity`: West Michigan, 300 MW, towers 2.36 to 3.60 MGD (+53%), hybrid 1.53 to 2.38 (+56%), assist 1.07 to 1.65 (+54%), closed loop unchanged. No page layout changes.

**Assessed or not assessed.** "No listing" read the same for a clean water and one the state never assessed. The snapshot's downstream path and site data now carry `a`, and `Reach.assessed` reaches the package, in every state.

**The water system a place is compared with.** The largest by population won at any overlap: Westerville, Ohio (its own system at 99.7% of the place) was set against Columbus at 0.8%. New rule [A]: a system covering at least half of the place (largest share if more than one); otherwise the largest by population among those covering at least 5%; otherwise the largest by population. Plain largest share was tested and rejected: it picks Four Way SUD over Lufkin for Angelina County, Texas, and small systems in many places. `comparisons.main_system` and `WQ.mainSystem` are held together by `engine.check_parity`, which compares the system chosen in every place in every state. Known limits: shares come from mapped boundaries, which overlap. Holland, Michigan goes to Holland Township Consolidated at 52% over Holland Board of Public Works at 44%, and Miami Township, Ohio to Cleves at 51% over Cincinnati at 46%. In sparsely served counties a small system over 5% can beat a city system under it: Wilbarger County, Texas goes to RRA Lockett over Vernon, and Greene County, Virginia to Mountain Lakes over the county's own system.

**Utility peaks.** EIA-861 has Duke Energy Ohio at a 914 MW summer peak against 2,252 MW of average load from its sales, which is impossible. A peak below the average load now counts as missing, in every state, and that comparison is left out (`waterledger_data.power.usable_peak`).

**Stated, not changed.**

- Assist control. The model runs pads at full effectiveness above the switch temperature. Holding the air only at the switch temperature would evaporate, on central parameters over ERA5 1995-2024: West Michigan 41% less on average and 8% less on the peak day; Columbus 33 and 4; Ashburn 26 and 2; Austin 13 and 4; Houston 12 and 3. The review's trial gave 42 and 19. The average agrees and the peak does not; its peak-day figure was not reproduced here. Controls are not published, so the higher estimate stands [A].
- Cycles of concentration, 3-7, against DOE FEMP BMP #10's two to four typical and six or more possible. No figure for large campuses is published. Withdrawn is evaporation x cycles / (cycles - 1), so at the middle of each range FEMP's typical range would take 1.5 / 1.25 = 20% more water, all of it blowdown. It is the second driver of tower water in the sensitivity analysis.
- Line losses at EIA's national 5% in every state. A campus on the transmission system may lose less [A].

**Checks rerun on 1.6.** Cooling towers, air-cooled computers, 300 draws, station weather 2005-2024, 5-95% PUE against Lei and Masanet's case 2: Houston 1.108-1.243 (1.099-1.250), McAllen 1.112-1.260, Fort Worth 1.099-1.224 (1.087-1.215), Lubbock 1.086-1.198 (1.080-1.192), Richmond 1.092-1.209 (1.084-1.202), Dulles 1.089-1.202, Columbus 1.087-1.198 (1.083-1.196), Cleveland 1.086-1.196, Las Vegas 1.082-1.192, Phoenix 1.089-1.204 (2B, 1.084-1.201). Closed loop over towers, medians: Cleveland +1.6%, Columbus +1.9%, Dulles +2.2%, Richmond +2.6%, Lubbock +4.1%, Houston +4.5%, Fort Worth +4.7%, McAllen +6.0%, Las Vegas +7.2%, Phoenix +8.4%. The methods pages' statements stand.

**Tests.** `tests/test_hand_values.py` has values worked by hand with their numbers written out, including a lake case. HFG halved, LATENT_KJ halved, KG_GAL = 1, the evaporative ratio coefficient x10, outside air flow x10 and lake latent heat /10 had passed everything but the golden files, and now fail. `test_water_balance` passed only because its weather was January, with no condensate, and now runs on weather that condenses.

**Data release.** 2026-11-01 was published twice, first with model 1.4 and then 1.5, against design 0003's rule. Snapshots now never change: see the design note. Packages before 3.8.1 read `latest`, frozen on model 1.5. A run of 3.7.1 on the 1.5 data reports model 1.5, with its wastewater middle leaving out condensate while its range includes it (Houston closed loop 0.0062 MGD, range 0.0062-0.0244); it still closes on what it reports. Michigan's manifest had `checks: null` because its writer hard-coded it: its three tests ran and passed, while the statewide `check-snapshot` never ran for Michigan. It now does.

## Nov 1, 2026: toward model 1.7, the cooling model's parameters and peak day

From the parameter audit of model 1.6 (Northline's `docs/research/parameter-ledger-cooling.md`) and the decisions Andrew approved for 3.9 (his rule: reasonable, accurate, reality based). The version moves when the groups are integrated. Measured below at 300 MW with staff water, 1995-2024 weather, 200 draws, seed 7, medians in MGD: West Michigan's Gaines cell on the Open-Meteo record; Cleveland, Dulles, Houston and Lubbock on stations. Each change was run on the one before it, in the order given here.

**Sampling.** Independent uniform draws are replaced by a Latin hypercube, seeded, with one sampler (`physics.sample_parameters`) behind the per-run loop, the ensembles and, with its own ranges, the lake. Lei and Masanet used 50 Latin hypercube samples. Each parameter has its own random stream keyed by name, so adding one leaves the rest alone, which is what made the later comparisons here paired. The old streams, kept so that earlier draws would not change, are gone.

Parameters describing one plant now move together: a well-built plant (UPS, distribution, fans, pumps, pressure drops, approaches, coil and chiller quality); one temperature design (supply air, air rise, water rise, tower range, which a plate exchanger ties together); and AI campuses (utilization, load factor, liquid share, liquid water temperature). Cycles of concentration is left out because it follows source water, a matter of place. Each group has a shared score; a member's rank order follows shared score + its own score with equal weights, which gives two members a rank correlation of about 0.5, and every parameter keeps one draw in each stratum (rank reordering, after Iman and Conover 1982). No published correlation exists, so 0.5 is an assumption [A], midway between independence and the comonotone bound the audit ran.

Staff water stays on its own uniform draws, as before.

Effect, almost entirely on bands and on noise from the old draws: towers withdrawn +0.5 to +1.6%; towers consumed +2.5%; returned +6%; annual PUE -0.1 to -1.0%, its band wider (Houston towers 1.088-1.196 to 1.073-1.228).

Convergence at n = 200, on the final parameters, 12 seeds, Gaines and Houston, cooling water alone at 300 MW; 95% half-width of each percentile as 2 standard deviations across seeds, Latin hypercube against independent draws of the same ranges:

| Output | p10 | p50 | p90 |
|---|---|---|---|
| Towers withdrawn, average | 1.7-2.8% (3.3-3.6%) | 1.9-2.1% (2.5-2.8%) | 2.3-2.6% (2.6-2.8%) |
| Towers withdrawn, peak day | 2.7-2.9% (3.8-4.1%) | 1.9-2.1% (2.8-2.9%) | 2.3-2.7% (3.3-3.6%) |
| Annual PUE, all three wet designs | 0.2-0.5% (0.6-0.8%) | 0.4-0.7% (0.6-1.1%) | 0.4-0.7% (0.7-1.2%) |
| Hybrid withdrawn, average | 21-60% (32-57%) | 5.8-11% (12-18%) | 3.8-4.6% (6.4-6.9%) |
| Hybrid withdrawn, peak day | 2.2-16% (9.9-18%) | 1.7-3.1% (5.0-5.5%) | 3.2% (4.1-5.2%) |
| Assist withdrawn, average | 25-66% (32-64%) | 7.7-16% (9.4-18%) | 6.5% (6.6-7.6%) |
| Assist withdrawn, peak day | 10-19% (13-24%) | 3.0-8.2% (5.8-7.9%) | 5.1-6.6% (5.7-6.6%) |

Towers and PUE have converged. Medians and upper ends of hybrid and assist are usable, at the widths shown. The low end of hybrid and assist averages has not converged: those are small numbers from a long tail of plants that hardly go wet, and the mean of 12 seeds sits +8% (hybrid) and +17% (assist) above a single 1,000-draw run in Gaines, against -3% and +3% in Houston. In Gaines they amount to about 0.01 MGD at 300 MW. The hypercube gains little there, since one tail is set by a few interacting parameters. It should be read as "near zero", or the published builds should use more draws. The count stays at 200 here; run time scales with it.

**Peak day (decision 1).** The headline peak day and the record day now run at average load / load factor, with the load factor 0.88-0.94 from EPRI (2026): 94% at a large hyperscale site, 88% at co-location sites. EPRI's pairs give 0.75 / 0.94 = 0.80 and 0.57 / 0.88 = 0.65 of capacity, against its measured peak utilization of 62-80%. Load factor is linked to utilization for that reason. The upper case stays: every computer at capacity all day, `withdrawn_peak_full_capacity`, now in the ensembles as well as the loop. Averages, months and years stay at average load. Loop top-ups and outside air go with capacity, so closed loop does not move. Hottest-hour electricity stays at full capacity, so the water and electricity peaks still describe different conditions, as stated in model 1.6. The lake has no peak day; its highest 30 days stay at average load. Effect on the peak day: towers +9.5 to +10.1%, hybrid +9.3 to +10.4%, assist +8.4 to +11.4%. Han et al.'s measured tower ratio of peak day to average, 2.21 at one zone, is still about 1.6 times the model's roughly 1.3-1.4. The model's towers remain flatter day to day than that zone.

**Cycles of concentration (decision 2).** 3-6, was 3-7. Lei and Masanet's Table 3, case 2, allows 3-15. The consumptive ratios in Han et al. (2026, Table 2), 0.72-0.91, are about 3.6-11 cycles, median about 4.5; ICPRB's 75% is 4. DOE FEMP BMP #10, cited for 3-7 until now, says two to four is typical and six or more possible, so it is lower than this range and is stated as such. Nothing is published for large campuses. The real limit is source water, which a later site input could carry. Effect: towers withdrawn +2.6 to +2.9%, returned +15%, consumed unchanged; hybrid withdrawn about +2.5%.

**Hybrid full-evaporation point.** Was 30-33 C in every state, which is West Michigan's design temperature, though its comment said the site's. Now each location's 0.4% design dry-bulb from its own hourly record, whatever that record is (`physics.design_dry_bulb`, so a station or a grid cell), +/-1.5 K [A]. The source patent has no such point, so the top of the ramp remains an assumption, tied now to something that differs by place: Gaines 31.0 C, Cleveland 32.2, Dulles 33.9, Houston 36.7, Lubbock 37.8. A run with a location's design temperature at or below its switch point still ramps over 1 K above the switch [A]. The value cannot be defaulted: hybrid raises an error without it, because a fixed default is how this error came about. Models that receive weather one hour at a time set `design_db`. Effect on hybrid withdrawn: Gaines +2.5%, Cleveland -9%, Dulles -22%, Houston -34%, Lubbock -36%; peak day +3.7%, -4.6%, -11%, -24%, -22%.

**Switch points (decision 3).** When a dry cooler goes wet is an operator's setting, not a property of the equipment: the patent has the customer set it, Trane's DC-WPR004A says the customer chooses, and EVAPCO calls it a selection and control output. Drawn on its own, a site with 45 C liquid water could go wet at 21 C while one with 19 C air-loop water stayed dry to 28 C, running air-cooled chillers. So the setting is now tied to the loop:

    loop limit = air share x air loop water + (1 - air share) x liquid water - dry cooler approach
    air loop water = supply air + air rise - air rise / coil effectiveness
    switch point = loop limit + margin (-2 to +2 K [A]), held within 21.1-35.1 C

The limit is the dry-bulb where the dry coil can no longer hold loop supply. The margin covers operators who go wet early or trim with chillers longer. The bounds are the 70-95 F the patent gives for customer settings; applying them to assist is by analogy [A]. Assist and hybrid share one setting. The Uptime Institute 20 C citation is dropped: the audit could not find it in anything readable. A site can fix the setting with `switch_on`. Across the draws the limit runs 18.5 / 24.2 / 30.4 C (p10, p50, p90), the setting 21.1 / 24.2 / 30.6, with a quarter of draws at the 21.1 floor and under 1% at the top. Balances close as before, and the assist's air-side balance uses the new setting. Effect on withdrawn: hybrid +2 to +9%, assist +3 to +25% (largest in the coolest climates); peak day within -4.7 to +5.2%. Bands widen a lot: Gaines hybrid average 0.040-0.150 to 0.013-0.170, since a warm liquid loop may hardly go wet in Michigan and a cold air loop goes wet often.

**Hybrid peak by place.** With the two changes above a hybrid's median peak day is about the same everywhere, 1.7-1.8 MGD at 300 MW, because each location reaches full evaporation near its own hottest weather. That follows from the assumption that plants are sized to their climate. It should be stated when peak days are compared between climates.

**Evaporative ratio (decision 4).** Kept. LBNL (2024) and Lei and Masanet evaporate all the heat (Lei Eq. 5); this model uses the Rutberg et al. (2011) ratio as USGS SIR 2013-5188 does, so a share of the heat leaves as sensible heat in the air. Towers come out below those two sources: makeup, median, 1.58 L per IT kWh in Gaines, 1.60 Cleveland, 1.63 Dulles, 1.76 Houston, 1.67 Lubbock, against about 2.2 (Lei case 2, read off a figure, about +/-0.1; LBNL Fig. 4.4), which is 20-28% lower. Reasons: the air's own heat balance says not all the heat goes to evaporation, except in hot dry hours; USGS uses the same relation as an upper limit in cool months and models towers with evaporative ratios below 1; and no disclosed fleet reaches 2.2 (Han Table 2, 2024: consumed 1.13-1.36 against the model's 1.25-1.38 for all-tower sites, and those fleets are mixed). That is an argument, not a measurement: no site-level metered tower check exists. A known limit in the other direction: Rutberg has no humidity term and the ratio is capped at 1, so west Texas towers may run about 6% low annually and 10-14% low in hot dry hours, from a simple air-side bracket.

**Citations corrected.**

- Tower evaporative ratio: USGS's 5-15% (p. 24, Leung and Moore) and 15% added to the tower suite (p. 28). Its +/-18% for towers is consumption with heat error included (p. 29), and its 18% for the ratio itself is for water surfaces. The range, -0.10 to +0.05, stands.
- Loop volume: Vantage's 11.8 million gallons is out. It came from a TV tour of Sterling, Virginia, not Port Washington, and no capacity was given. Crusoe's text gives about 1.7 million gal for a typical system, without tying it to 200 MW in the text. The top of 12,000 gal/MW is marked [A]. A search found a Lake County, Illinois document said to give 3.2 million gal of flush and fill for a 200 MW building, about 16,000 gal/MW, but it refused automated reads, so it is not used and is worth reading by hand. No numbers change.
- EVAPCO's pad test is dated as presented, CTI, Feb 2019, and is a maker's own.
- Open-Meteo: the request sets no `models`, so best match applies, which combines IFS HRES (from 2017), ERA5 and ERA5-Land. It is now described that way in the models package. The source itself changes in the next release. The default time zone is the point's own rather than Detroit.

**Lake source.** The heat balance uses Ward's wind function, which USGS prints as an example (Eq. 14). USGS's own lake estimates used Webster and Sherman (1995), and it did not use functions that reach zero at no wind (p. 27). This is now stated as a departure. It is kept because winds are sampled at 5-15 mph, where USGS puts the spread between wind functions at about 12% (p. 28, at 4.5 mph). Webster and Sherman's coefficients are not in the USGS report and were not read. USGS's error for this ratio is now carried: 21% on the Great Lakes (p. 29), `evap_error` 0.79-1.21, so 1.0 at the center. Effect at 100 MW on Lake Michigan: forced evaporation 0.232 / 0.293 / 0.359 to 0.229 / 0.294 / 0.375 MGD, withdrawal 38.2 / 48.4 / 63.7 to 37.6 / 48.7 / 65.3 (the Latin hypercube only).

**Smaller.** Tower range 7.2-10.8 F, was 7-15, whose top had no source. Drift 0.005-0.02% of flow, was 0.0005-0.02%, whose low end was ten times under its citation. Together: towers withdrawn +0.2 to +0.3%, consumed +0.5 to +0.9%, returned -2.2%, annual PUE up to +0.3%, since a narrower range means more tower flow and warmer chiller condensers.

**UPS, not changed.** The narrowing to 95-99% was considered and not made. Lei and Masanet and LBNL both give 90-99%, ENERGY STAR's page gives 92-95% for new efficient units, and no measured campus figure was found. Fleet PUEs of 1.08-1.16 argue against 90% (it alone would give 1.11), which supports raising the floor, but nothing supports 95% as the number. It would lower annual PUE about 3% (Dulles towers 1.128 to 1.096) and take towers below LBNL's 1.12. It stays in Open, as a question for someone with measured data.

**Total effect, model 1.6 to this group's changes.** Medians, MGD at 300 MW, with staff water.

| Place | Design | Withdrawn | Consumed | Returned | Peak day | Annual PUE |
|---|---|---|---|---|---|---|
| MI Gaines | closed loop | 0.007 to 0.007 | 0.001 to 0.001 | 0.008 to 0.008 | 0.009 to 0.009 | 1.126 to 1.117 |
| | assist | 0.077 to 0.086 | 0.060 to 0.066 | 0.018 to 0.018 | 1.07 to 1.22 | 1.121 to 1.114 |
| | hybrid | 0.078 to 0.086 | 0.056 to 0.062 | 0.020 to 0.024 | 1.56 to 1.79 | 1.123 to 1.115 |
| | towers | 1.89 to 1.98 | 1.51 to 1.56 | 0.342 to 0.413 | 2.36 to 2.69 | 1.124 to 1.117 |
| OH Cleveland | closed loop | 0.007 to 0.007 | 0.001 to 0.001 | 0.008 to 0.008 | 0.009 to 0.009 | 1.130 to 1.120 |
| | assist | 0.100 to 0.111 | 0.079 to 0.085 | 0.022 to 0.023 | 1.19 to 1.37 | 1.126 to 1.118 |
| | hybrid | 0.105 to 0.102 | 0.078 to 0.075 | 0.025 to 0.027 | 1.62 to 1.72 | 1.128 to 1.118 |
| | towers | 1.92 to 2.00 | 1.53 to 1.58 | 0.347 to 0.418 | 2.38 to 2.71 | 1.125 to 1.118 |
| VA Dulles | closed loop | 0.007 to 0.007 | 0.001 to 0.001 | 0.009 to 0.009 | 0.008 to 0.008 | 1.139 to 1.128 |
| | assist | 0.163 to 0.175 | 0.130 to 0.137 | 0.033 to 0.033 | 1.56 to 1.72 | 1.130 to 1.124 |
| | hybrid | 0.183 to 0.155 | 0.141 to 0.120 | 0.042 to 0.038 | 1.85 to 1.84 | 1.131 to 1.124 |
| | towers | 1.96 to 2.04 | 1.56 to 1.61 | 0.356 to 0.427 | 2.44 to 2.78 | 1.127 to 1.120 |
| TX Houston | closed loop | 0.007 to 0.007 | 0.001 to 0.001 | 0.016 to 0.016 | 0.008 to 0.008 | 1.177 to 1.167 |
| | assist | 0.373 to 0.400 | 0.304 to 0.315 | 0.081 to 0.076 | 1.73 to 1.91 | 1.164 to 1.156 |
| | hybrid | 0.505 to 0.358 | 0.403 to 0.284 | 0.107 to 0.082 | 2.08 to 1.81 | 1.159 to 1.159 |
| | towers | 2.13 to 2.20 | 1.69 to 1.74 | 0.389 to 0.466 | 2.50 to 2.84 | 1.148 to 1.141 |
| TX Lubbock | closed loop | 0.007 to 0.007 | 0.001 to 0.001 | 0.007 to 0.007 | 0.008 to 0.008 | 1.152 to 1.144 |
| | assist | 0.352 to 0.362 | 0.287 to 0.296 | 0.067 to 0.065 | 2.01 to 2.19 | 1.133 to 1.128 |
| | hybrid | 0.352 to 0.239 | 0.276 to 0.187 | 0.071 to 0.053 | 2.05 to 1.81 | 1.132 to 1.132 |
| | towers | 2.00 to 2.08 | 1.59 to 1.65 | 0.362 to 0.434 | 2.42 to 2.75 | 1.125 to 1.118 |

**Against disclosed values.** Hybrid consumed, L per IT kWh, median (p10-p90): Dulles 0.093 (0.019-0.167) against Microsoft Virginia's projected 0.14 and Meta's fleet 0.19. Houston 0.219 (0.059-0.367) and Lubbock 0.147 (0.053-0.231) against Microsoft Texas's 0.25, where model 1.6 stood above it. Gaines 0.050 (0.005-0.104) against LBNL's 0.05-0.55. The medians now sit below the operators' figures rather than above them in Texas. Those disclosures are in the bands except Meta's fleet and, narrowly, Microsoft Texas at Lubbock. They are fleet or state figures with unknown design mixes, so this does not contradict the change, but it suggests the assumption of a plant sized to its climate may be on the low side. A metered hybrid or adiabatic site would settle it.

**Tests.** `tests/test_hand_values.py` adds the peak utilization, design dry-bulb, ramp, switch point with its bounds, assist water at a switch point and the lake's error, with numbers written out. `test_physics_properties.py` holds one draw per stratum, reproducibility and the linked rank correlations. Balance tests hold. The ensembles and the loop agree, the upper case included.
## Nov 1, 2026: power plants by water body, fresh and saline, coal and nuclear in every state (for model 1.7)

**The inputs were rebuilt.** The work folder behind `power_water/` isn't kept anywhere, and the audit could not rerun it. It was rebuilt from EIA's public files (2022-2024 cooling detail, EIA-860 2024, EIA-923 2022-2024, State Electricity Profiles, API plant and state generation), and `states.py`, `ba_compare.py`, `imports.py` and `combine.py` before any change reproduced the table exactly, including phi 0.45 and 0.60 and the import shares. `verify_table.py` matches every intensity in `grid_water_2022.csv`. EIA-930 was not fetched and `reconcile.py` was not rerun: its r values compare Siddik et al. with raw reports, which the cooling class does not touch, so r stands. The O and C columns in `recon_ba_2022_2024.csv` and the tables in `reconciliation.md` are from before this change.

**Decision (Andrew, Nov 1): classify plants by water body in every state.** EIA's code says how water moves through a plant, not where it comes from. A plant that draws from a built reservoir and returns the water to it is circulating the reservoir, and the reservoir is its cooling pond. That water isn't taken from a river, and counting it as once-through put North Anna's circulation in Virginia's withdrawn figure.

Rule, the same everywhere (`cooling_water_bodies.csv`): fresh water; a built reservoir; drawn from and returned to the same one; and not a river main stem, where the river passing through far exceeds the plant's flow (Sequoyah, Peach Bottom, Arkansas Nuclear One stay once-through). That last test is a reading of where the reservoir sits, not a computed flow ratio [A]. Such a plant takes pond class whatever its EIA code. The existing rule then applies: over 25,000 gal/MWh is circulation, replaced by Macknick et al. (2012) pond medians, and zero consumption is replaced likewise. Natural lakes and the Great Lakes stay once-through. Every once-through plant on a source named as a lake, reservoir, pond or canal, or with EIA code OC or a pond area, was reviewed: 69 plants, 27 of them reservoirs.

Checked against sources:
- North Anna. EIA-860 6_2 Cooling codes it ON, source and discharge Lake Anna, fresh. NRC NUREG-1437 Supplement 7 (2002), ch. 2: the lake was made in 1971 by damming the North Anna River as the plant's cooling source, and about 1.9 million gpm passes through the condensers to the Waste Heat Treatment Facility, a diked part of the lake. That flow is about 2,700 MGD; EIA's 871,586 Mgal in 2024 is about 2,380 MGD. So the audit's note holds, and the report is real circulation, not an error.
- Surry. EIA-860: ON, James River, brackish. NRC's subsequent license renewal review: once-through from the James River and back to it, about 3% of tidal flow, and the river brackish enough that the station uses wells for fresh water. It stays once-through, all saline.
- Michigan: none. Cook, Campbell, Monroe, Belle River and Dearborn draw on the Great Lakes and connecting waters; Greenwood and Midland were already pond class.
- Ohio: none. Ohio River and Lake Erie.
- Virginia: North Anna only.
- Texas: Parish, Sim Gideon, Lost Pines, Handley, Knox Lee, Miller, Mountain Creek, Olinger, Dansby and Ferguson join the pond plants (TWDB reservoir pages, cited row by row). TWDB's pages for Lake Arlington, Palo Pinto and Lavon don't mention cooling; those rest on EIA-860's source and discharge. EIA-860 names Lake Fayette for Ferguson, while LCRA and TWDB place it on Lake LBJ; the class is the same. Barney Davis and Cedar Bayou have EIA code OC and ponds, but draw saline bay water and stay once-through, saline.
- The other states' 16 reservoirs are by EIA-860 fields and name only. They are not published states; check them before those states are.

**Consumption moved more than expected, for a good reason.** Reservoir plants reporting zero consumption now take the pond median instead of the once-through one, which is the rule's plain result. North Anna goes from 269 to 610 gal/MWh and Virginia's state figure rises 23%. The energy balance supports it: a reactor at 33% efficiency rejects 2.03 MWh of heat per MWh sent out, 7.3 GJ. If three quarters leaves as evaporation, at 2.45 MJ/kg, that is 2,240 kg or 591 gallons. Once-through medians are lower because the heat goes to a much larger body of water, where the evaporation it causes is harder to attribute; they are left as they are.

**Fresh and saline.** The table now carries `withdrawn_fresh_l_per_kwh` and `withdrawn_saline_l_per_kwh`, which add to withdrawn. EIA water type by cooling system, Saline and Brackish together; Reclaimed and Other count as fresh, apart from Haynes and Scattergood (Pacific Ocean, typed Other). The split is the plant-based share in the state and its main balancing authority, weighted by imports, applied to the central value; there are no separate ranges. Reported saline plants stay saline; plants filled at tower medians count as fresh [A]. `PlantWater` and `PowerPlantWater` report both where the plants are known. Grid averages and new gas have no split, and grid averages stay as Siddik et al. published them, circulation included.

**A wider withdrawal range.** The shared error on Macknick-filled withdrawal used nuclear once-through consumption's spread, 0.35. Those plants are now nearly all reservoirs, and Table 3's nuclear pond range is 500-13,000 gal/MWh, so ln(13000/500)/4 = 0.81 [A]. Texas's range, 4.6-37.3 L/kWh, is wide because Texas's central value rests largely on those medians. Before, it looked narrower than the evidence is.

**Coal and nuclear options in every state** (`fuels.py`, `tables/state_fuel_water_2024.csv`, `energy.fuel_options`). Macknick Tables 2 and 3 for how the state's plants are cooled, medians and ends, weighted by 2024 generation: Michigan's existing method, now everyone's, with Michigan's values unchanged within a tenth of a percent. Medians rather than plant reports because a single report can swing a small state's option (Clover, in Virginia, reports 57 gal/MWh consumed through towers); the screened reports sit in the table as a check. A state without a fuel in 2024 has no option for it. Nuclear is the thirstiest option in all four states, so `thirstiest_power` now answers alike. The options' notes name no plant or water body, Michigan's included.

**Smaller items.**
- New gas note: the clause on Michigan's combined-cycle plants is gone; it was true only of Michigan and appeared everywhere.
- Wind and solar weight for a place with no plant-based figure: its own 2024 generation from EIA (Alaska 0.0593, Puerto Rico 0.6293), not Michigan's. A state with no generation record takes the U.S. share over the table, 0.327, the only value that favors no state. The factor is at most 5 gal/MWh, so this is about being right rather than about size.
- Michigan's utilities now carry a balancing authority and grid water, as other states' do. The snapshot's rule put everyone but Indiana Michigan Power in MISO; the service territory layer and EIA-861 also put Dowagiac, Midwest Energy Cooperative, Niles, Paw Paw, South Haven and Sturgis in PJM.
- Line losses stay at 5%: EIA FAQ 105 says what it was cited for. The biopower dry factor, 35 gal/MWh, is Macknick's biogas value, now marked [A]; it touches a negligible share.

**Measured.** Withdrawn and consumed at power plants, state mix, gal/MWh, and for a 300 MW campus on towers (217-221 MW average, losses included), MGD:

| State | Consumed gal/MWh | Withdrawn gal/MWh | Consumed MGD | Withdrawn MGD | Fresh / saline MGD |
|---|---|---|---|---|---|
| MI | 268 to 268 | 15,459 to 15,476 | 1.469 to 1.469 | 84.9 to 84.9 | 84.9 / 0 |
| OH | 279 to 280 | 6,425 to 6,261 | 1.531 to 1.537 | 35.3 to 34.4 | 32.3 / 2.0 |
| VA | 178 to 218 | 13,704 to 8,148 | 0.976 to 1.198 | 75.3 to 44.8 | 17.4 / 27.4 |
| TX | 202 to 206 | 5,074 to 3,446 | 1.129 to 1.150 | 28.4 to 19.3 | 12.2 / 7.0 |

Elsewhere, 17 states' withdrawn moves over 2%, led by West Virginia (-80%), South Carolina (-62%), North Carolina (-59%) and North Dakota (-36%); North Carolina's consumption rises most, 30%. The median state's consumption doesn't move.
## Nov 1, 2026: runoff, comparisons and defaults, for model 1.7

Measured at 300 MW, cooling towers, on the published snapshots; the rebuild at integration moves water and power on top of this. Sample places: Gaines charter township MI, Jerome Township OH, Loudoun County VA and Hays County TX (200 acres of farmland, as a township or county starts), and Grand Rapids, Columbus, Leesburg and Abilene (50 acres, built).

| 200 acres of farmland | MI | OH | VA | TX |
|---|---|---|---|---|
| Runoff today, million gallons a year | 12.4 to 39.3 | 13.1 to 41.4 | 14.1 to 44.6 | 11.7 to 36.9 |
| Runoff after | 91.3 to 105 | 96.2 to 111 | 104 to 119 | 85.9 to 98.8 |
| Sediment today, tons a year | 99 to 16.5 | 99 to 17.4 | 99 to 18.8 | 99 to 15.5 |
| Sediment after, typical wet ponds | 10.8 to 15.2 | 11.4 to 16.0 | 12.3 to 17.3 | 10.2 to 14.3 |
| Sediment after, no controls (new) | 47.5 | 50.1 | 54.0 | 44.7 |
| Sediment during construction | 20,000 to 228 | 20,000 to 240 | 20,000 to 259 | 20,000 to 214 |
| Phosphorus today, pounds a year | 107 to 168 | 108 to 177 | 110 to 191 | 105 to 158 |
| Phosphorus after, typical wet ponds | 70 to 168 | 74 to 177 | 80 to 191 | 66 to 158 |
| Phosphorus after, no controls (new) | 297 | 313 | 338 | 279 |
| Home, gallons a day | 300 to 173 | 300 to 158 | 300 to 216 | 300 to 240 |
| Homes, the campus's water | 6,298 to 10,922 | 6,443 to 12,221 | 6,513 to 9,053 | 7,109 to 8,885 |

**Runoff coefficients.** A pervious coefficient of 0.05 on every surface was the intercept of Schueler's site-scale regression, used as if it were a land cover's value. The Runoff Reduction technical memo (Hirschman, Collins and Schueler 2008, Table 4, the basis of Virginia's method) gives turf 0.15, 0.20, 0.22 and 0.25 on soil groups A to D and forest 0.02-0.05, and impervious 0.95. Decision: turf 0.20 and forest 0.03 (group B), by soil group later. Cropland isn't in the table. It keeps 0.20 [A], not a lawn value by accident but because row crops on group B have curve numbers of 78-81 against lawn's 61-69 (TR-55 Table 2-2), so they shed at least what a lawn does; tile drains take some of what would run off, which pulls the other way. Woods take forest's value, including where a reader means meadow (curve number 58). Built land's pervious part is turf. After against today falls from 7.4 to 2.7 times on farmland. The finished site's coefficient is 0.575 at half impervious, where Schueler's regression gives 0.50. Separately, the row crop curve number was 72, labeled row crops or meadow; TR-55 has 78 for straight row in good condition on group B, 81 poor, and 58 for meadow. It is now 78. Only Northline's engine reads it.

**Sediment on one basis.** Replaced the same day; see "sediment on a yield basis" below. Today's farmland was an assumed delivered soil loss of 0.5 tons an acre, which implied 2,730 mg/L in the old runoff, against the model's own 100 mg/L. The construction row was gross erosion, 100 tons an acre. Set side by side they gave 200 times, where EPA Fact Sheet 2.6 says 10 to 20. Today is now runoff x concentration for sediment and phosphorus alike, and the soil's phosphorus is no longer added on top of a concentration that already contains it. Construction needed the same basis, and the model has no construction concentration. It is farmland's times EPA's ratio, end for end: 50 x 10, 100 x 15 and 160 x 20, or 500, 1,500 and 3,200 mg/L, on bare ground at turf's coefficient [A]. So the ratio is used rather than checked; the independent check is the concentration itself. The Minnesota Stormwater Manual's TSS page is reported to put construction runoff above 1,000 mg/L; we read that only as a search excerpt, because the page refused automated requests, so it needs a reader's confirmation before it is cited. Gross erosion stays as its own row, `soil_moved`, 30, 100 and 200 tons an acre (EPA MM8 Table 8.1), with no today beside it.

What this does not settle. Farmland at 100 mg/L gives 0.08 tons an acre a year. The old assumption was 0.5, and U.S. cropland's sheet and rill erosion averages 2.67 before any delivery (NRI 2017, through secondary reports). Field-edge runoff is, in our judgment and without a citation here, often above MPCA's 50-160, so today's farmland sediment is probably low, which makes the campus look worse by comparison on sediment than a field-edge figure would. Construction at 1.1 tons an acre is 90 times below gross erosion. Both follow from the decision to use the model's own concentrations. A state-specific delivered rate (NRI Table 14, or RUSLE's R) would be the next step.

**Stormwater, both cases.** Every output now has the load with no controls and with typical wet ponds: rows `mud`, `mud_no_controls`, `p`, `p_no_controls`, each with `controls`. No state's rule is assumed to apply. 80% TSS is what wet ponds typically do, from the Center for Watershed Protection's national database (2000), as printed in SEMCOG 2008 Table 9.5, which also gives TP 51 and TN 33. It happens to be Michigan's standard too; that text stays in `controls.standard` for Michigan's pages. The BMP Database citation for 0.51 was wrong. Nitrogen was 0.26, cited to a BMP Database report nobody could open; it is now 0.33 from the same table as the other two, so all three removals have one source. No row reads nitrogen.

**Means for loads.** A load is concentration x water, so it needs the mean, and most of what was here were geometric means. For a lognormal, mean = median x sqrt(1 + COV^2). NSQD 1.1 (Maestre and Pitt 2005, Table 3) gives medians and COVs by land use across U.S. municipalities. Choices:

- Pavement has no NSQD category, since NSQD samples outfalls. Commercial, industrial and freeway outfalls are low, middle and high: TSS 96, 153 and 276; TP 0.34, 0.43 and 0.51; TN 2.9, 3.0 and 3.9. Marquette's parking lots are not used, which settles the 138 that included data USGS flags as unreliable. Their clean 110, as a mean at industrial's COV, is 208, inside the range. MPCA's commercial 75 falls below it.
- Roofs have no national source. Marquette's commercial roofs (24, 0.09, TKN 1.7 + NO 0.57) as means at NSQD commercial's COVs: 54, 0.14, 3.1. Low end MPCA's.
- Turf: MPCA's open space low, NSQD open space middle, mixed open space or open space's own COV high. TSS 21, 87, 147; TP 0.19, 0.46, 1.13; TN 1.5, 1.79, 2.38. Open space's TP COV, 3.5 on 68 events, reflects a few extreme values, so its middle uses mixed open space's 1.1 [A]. Marquette's lawns (TSS 262, TP 2.33) and Madison's (TP 2.67) are not used: source-area samples from residential lawns [A]. A campus with fertilized turf could run above this.
- Farmland: no national mean. TP's middle moves from STEPL's 0.3 to MPCA's review median 0.533, the value we could actually read, with 0.75 as a mean at COV 1 [A] for the high end. TSS stays MPCA's 50-160, which MPCA recommends no value from; 100 is its middle [A]. Woods stay MPCA's. TN stays STEPL's, unread.
- Built land's roofs and paving are the campus's mix, at the same roof share.

Check against what they were not fitted to, as a whole: the finished site with no controls runs 108 mg/L of TSS, between NSQD commercial's mean of 96 and industrial's 153, with 0.23 tons of sediment and 1.4 pounds of phosphorus an acre a year.

**A home's water.** EPA WaterSense's "more than 300 gallons" is an average family's, stated as such; it was being used as a home. A home is now the state's USGS 2015 water delivered to homes plus self-supplied domestic water, summed over counties, over the state's households in the same year (ACS 2015 1-year, table B11001): MI 173, OH 158, VA 216, TX 240. All 50 states and D.C. are in `waterledger_data.wateruse.HOUSEHOLDS_2015`, and any state's snapshot already carries the USGS layer, so a new state needs nothing else. It is indoors and outdoors, as USGS counts it, and for a state's average, not a place's. As a check, USGS's national domestic use is 77 gallons a person a day (Circular 1441), or about 190 a household. The Census API now needs a key, so the table was read from the Census Bureau's summary files; the table is in the package and nothing is fetched at run time. A percent of a system's connections moves with it, by the same ratio: Columbus 2.3 to 4.3%. Without a USGS layer, the figure falls back to EPA's and the comparison's basis says so.

**Michigan's rules on their own periods.** Part 327 defines a large quantity withdrawal over 30 days, and it was tested on the peak day. It is now tested on the highest month's average day, which the model already kept, with the peak-day reading beside it (`withdrawal_line_peak_day`, `withdrawal_period`). The permit line for hybrid cooling in West Michigan moves from 395 to 773 MW, and for towers from 256 to 273. The Compact's period is 90 days and it was tested on the annual average. No 90-day figure existed, so the models gained a statistic, `max_90day`, kept for water withdrawn and consumed; it needs the rebuild to appear in snapshots, and until then the Compact test stays on the average and says so (`great_lakes_period`). On the stored two years of West Michigan weather, the 90-day figure is 1.08 times the average for towers and 3.4 times for hybrid. Lake-source uses its highest month, which is no lower than any 90 days. With reuse on site, the highest month takes the share reuse saves on an average day [A].

A caution for the reader of the rule: EGLE's pages describe the thresholds by the capacity to withdraw, not what is used, and wells are sized for the peak. So the peak-day reading may well be the one a real application meets. The two are shown together for that reason.

**Withdrawal levels elsewhere.** Bands at 0.5 and 5 MGD were tried here and replaced the same day; see "The calculator is a what-if" below.

**Road salt, one method.** Michigan had 20-60 events by assumption, and elsewhere a multiplier of 0.6 fitted to bring Michigan's stations to that assumption. Michigan now uses the same method as the others: `runoff.salt_events`, the median winter's days with precipitation at 1 C or below, x 0.6, +/-50%, none below 2 days. The method is written to work on an ERA5 cell's hours too. The 0.6 has its own evidence now. A salting event is taken to be a day with measurable snow [A], and NOAA's 1991-2020 normal days with 0.1 in or more of snow over those days has a median of 0.62 across the 17 stations with normals in the four states (0.39-0.74), and 0.60 without Michigan's. That supports the ratio of days. It is not a measurement of what any parking lot's operator does, for which we found no national source; private lots may salt more often, including for frost, and freezing rain counts in neither figure. Michigan's regions: Ann Arbor 59 days, Kalamazoo 64, Grand Rapids 72, Lansing 71, Saginaw 64, Traverse City 89, Alpena 88, Hancock 119, or 35 to 71 events against 40. Marquette's airports report no precipitation in ISD-Lite, so Hancock, the nearest that does, stands for the Upper Peninsula. A July-June year now counts only with precipitation reported on half its days. Without this such a station read as no salt. A station reporting none is now an error. The sampled medians elsewhere did not move.

**Land default.** `kind == "city"` left out Ohio's villages and Virginia's and Texas's towns, so Leesburg, Virginia, started as 200 acres of farmland. Incorporated places now start at 50 acres built: Census's places layer other than census-designated places, through `Place.level` and `Place.incorporated`. New England's and New York's towns are county subdivisions and mostly rural, so they don't count. In the four snapshots, the places layer holds only cities, towns and villages. Michigan's kinds are unchanged. A very small incorporated town in West Texas now starts built, which is an assumption a reader can change.

**"Likely range" is the range across assumptions.** p10 and p90 of draws across parameter ranges we set are not a probability that the real value lies inside. Wording only.

## Nov 1, 2026: sediment on a yield basis

This replaces the concentration basis tried earlier today. Runoff x concentration gave farmland 0.08 tons an acre a year and construction 1.1. Those fail a reality test, because a concentration in runoff doesn't capture soil scoured off the ground: EPA's and USGS's measured construction yields are tens of tons an acre.

**Two bases, on purpose.** Today on soil (farmland, woods) and the construction years are yields: gross erosion x a delivery ratio. The finished site is runoff x concentration, because roofs, paving and established lawn aren't scouring. Built land today is also runoff x concentration, for the same reason. A comparison of today with the finished site therefore crosses bases, and it should be read as an order of magnitude. These are screening estimates: a study with site soils, slopes and sediment modeling would do better.

| 200 acres, 300 MW, sediment in tons a year | MI | OH | VA | TX |
|---|---|---|---|---|
| Today, original | 99 | 99 | 99 | 99 |
| Today, concentration basis (earlier today) | 16.5 | 17.4 | 18.8 | 15.5 |
| Today, yield | 106 | 141 | 156 | 130 |
| Finished, typical wet ponds | 15.2 | 16.0 | 17.3 | 14.3 |
| Finished, no controls | 47.5 | 50.1 | 54.0 | 44.7 |
| Construction year, no controls | 4,000 (600-13,200) | same | same | same |
| Construction year, sediment basins | 1,200 (36-7,656) | same | same | same |
| Soil moved, gross | 20,000 (6,000-40,000) | same | same | same |

**Farmland.** USDA NRCS's 2022 National Resources Inventory Summary Report, Table 15, gives sheet and rill erosion on cropland by state. Low is total cropland's median, middle its mean, high cultivated cropland's mean, because a load needs the mean: MI 0.58, 1.62, 1.88; OH 1.14, 2.16, 2.30; VA 1.10, 2.38, 3.56; TX 1.50, 1.99, 2.11; national 1.26, 2.67, 3.01. All 49 states in the table are in `runoff.CROPLAND_EROSION`, and a state not in it (Alaska, D.C.) takes the national row, not Michigan's. Wind erosion is not counted, which matters in West Texas. NRI's is one statewide rate, so a Texas place on the Blacklands and one on the High Plains read alike. Delivery is 0.2, 0.33 and 0.5 [A]: of what moves on a field, about a third leaves a site of a few hundred acres, the rest settling at field edges and in swales. The basis is area-based delivery tables: a USDA table (Stewart et al. 1978) has 0.33 at half a square mile, and an extension publication reports an agricultural figure of 25%, +/-15%. We read those only as a search excerpt of that publication, not the original. Michigan's middle comes to 0.53 tons an acre, close to the 0.5 assumed before, now with a source for the erosion and a stated ratio for the rest. Farmland phosphorus stays runoff x concentration, which holds its particulate part. The two aren't forced to agree: 0.53 tons at 0.04% phosphorus would carry 0.43 pounds an acre, against 0.77 from the concentration.

**Woods.** A yield as well, so it is on the same basis as farmland: EPA MM8 Table 8.1 gives natural rates from forests of 0.01-1.0 tons an acre (Washington), and under 0.5 in Franklin County, Florida. Its geometric middle of 0.1 [A] x the same delivery gives 0.002, 0.033 and 0.5. Runoff x concentration would have given 0.008, at the bottom of that range. The 0.5 high end is wide, and is left wide.

**Construction.** Gross erosion stays EPA MM8 Table 8.1's Wisconsin range, 30, 100 and 200 tons an acre a year, kept as `soil_moved`. Delivery for one year of disturbance is 0.1, 0.2 and 0.33 [A], giving 3, 20 and 66 tons an acre, or 600, 4,000 and 13,200 tons on 200 acres. The middle is below a field's delivery because a site isn't all bare all year, and it was set against measured yields, so it is partly a fit:

- Helsel 1985 (USGS WRI 84-4336, abstract read): 9,580-15,700 tons a square mile a year from an active highway construction area in Columbus, or 15.0-24.5 an acre. The middle is inside.
- Lee and Ziegler 2010 (USGS SIR 2010-5128, abstract read): 14.5 and 19.1 tons an acre with extensive controls, on erodible, steep ground; historic sites without controls 3.6-219. Our range is inside that except its low end, 3, just below 3.6. Our 6 tons an acre with basins runs below their measured 14.5-19, so the with-basin figure may be low.
- EPA MM8 Table 8.1: Franklin County, Florida, 30 tons an acre construction against 1.4 tilled and under 0.5 forest; Washington, D.C., 35-45; Anacostia 7.2-100.8. All read.
- Daniel et al. 1979 (about 8.6 an acre, Wisconsin) and USGS 1978's 60-80% reduction by controls were read only as search excerpts and are not relied on.

Against EPA's 10-20 times farmland: 37 in Michigan, 28 Ohio, 25 Virginia, 30 Texas, 23 on national rates; 21 in Franklin County's own figures. So the middle is above EPA's ratio. We did not force it. Bringing it inside would take 5-11 tons an acre in Michigan, under most readable measurements. EPA's ratio is from 1991 and compares with cropland erosion that was then higher than NRI's now (national 3.89 in 1982, 2.67 in 2022), and it is stated for gross erosion, where we get 37-62. The construction figure is the same in every state and doesn't follow rainfall, which is a limit of a single range from Wisconsin. A later version could scale by RUSLE's R.

**Sediment basins.** EPA MM8 Table 8.5 gives an average of 70% TSS removal, range 42-100%. We use 42, 70 and 94 (the table's perforated risers), since 100% is not a planning value [A], and take the whole site as draining to basins [A]. The row is `build_basin`.

**Removed.** The construction concentration, its bare-ground coefficient and the ratio-to-farmland setting.

## Nov 1, 2026: the calculator is a what-if

Estimates stay true to the physics, limits never change a number, and context tells people what to look out for. `tests/test_runoff_by_hand.py` runs Michigan and Ohio with every line and band pushed to both extremes and finds every estimated value unchanged.

**Where a state's rules aren't reviewed.** Michigan's lines were first used under other names, then neutral bands at 0.5 and 5 MGD. Both were lines we made up, and a reader takes "high" as a finding. Now there is no level for well pumping. `est.levels` gives the number (`withdrawal_mgd`, `withdrawal_peak_day_mgd`), the public supply of about how many people (`withdrawal_people`, at 138 gallons a person a day: USGS Circular 1441, 39,000 Mgal/d to 283 million people, which includes businesses and losses in the public supply), and `withdrawal_note`. At 300 MW of towers on wells, Jerome Township's 1.93 MGD reads as about 14,000 people. The national figure is used in every state; it is a comparison, not a rule.

**Where rules are reviewed (Michigan).** The legal lines stay. `withdrawal_flag` and `withdrawal_flag_peak_day` hold "permit", "zone_c" or nothing, on the rule's own period and on the peak day, with `withdrawal_flag_note` saying the estimated need exceeds the line and what follows. Zone C's line applies only in a Zone C area, and the package doesn't know a site's zone, so the note says so. EGLE's wording of those lines was read through search excerpts of its pages; the statute's Zone C clause was not found in the excerpt of MCL 324.32723 we read, and needs checking.

**Thresholds with no source, listed and not changed.** In `levels.py`: a water system's 2% and 10%; a plant's spare room at 10% and 50%; a small system at 5,000 connections or a quarter of them at peak; a plant near its size at 85%; a peak worth saying at 1.15; sediment "about as much" within 0.8-1.25; the verdict's "about the same" within 1.15. In `comparisons.py`: the main water system at 50% and 5% of the place; household wells at 10 before saying anything; the 50-acre built and 200-acre farmland starts. Elsewhere, affecting a default choice and so which numbers are shown: `SEWER_KM`, 10 km; a plant's 40 km and 0.5 MGD; and the rule that sends blowdown away from a plant whose spare room it exceeds. All are marked [A], and none alters the physics. The levels read as findings the way the withdrawal bands did, so the same question applies to them. The defaults are starting choices a reader can change, and they do change `to_sewer`.
## Nov 1, 2026: parity data, for model 1.7

Michigan came first, so several rules were written for it and others grew up separately in the national tier. Each is now one rule in every state, Michigan included. All measured against the published snapshots; nothing here moves until the states are rebuilt.

**Station records.** Two screens, the same everywhere (`waterledger_data.climate`).

A year counts only with 85% of its hours observed, the share the whole record already had to reach [A]. Years below it were being filled from the station's own means, which adds years of nothing but average weather and lowers the 1-in-10 peak's sample. Left out: Fort Worth NAS 1998-2006 and 2022 (10 years), Cotulla 1995-2000 and 2002 (7), Kimble County 1996-1999, 2001 and 2002 (6; 1997 is 2% observed), McAllen 1996 (1). Every station keeps at least 20 years.

An hour's temperature is suspect more than 10 C above the 99th percentile or 12 C below the 1st percentile of its month and hour, or more than 8 C from both hours beside it the same way [A]. It is removed unless one of the three nearest long-record stations within 150 km reported within 8 C in that hour or those beside it. The check against neighbors is what keeps real records. Margins alone would have removed Portland and Seattle in June 2021, more than 12 C past their 99th percentiles; with it, Portland keeps 46.1 C, Seattle 41.7 C and Phoenix 48.9 C. Reinstating tentative flags from neighbors follows HadISD (Dunn et al. 2012, Climate of the Past 8, tests 9 and 10), though HadISD's thresholds come from each station's distribution, not fixed margins. Removed: Abilene 5 hours (50.0 C at midnight in April 2022), Dayton 2, Kimble 2 (48.3 C in May 2024), Winkler 2, Dulles 1, Tri-State 1 (40.6 C in April 2002), McAllen 1 (-33.9 C), Victoria 1. Fort Worth's 53.9 C goes with its year. Cotulla's 46.7 C in June 2023 stays. Cotulla's 3.9 C on April 7, 2007, a likely real front, stays because its neighbors agree. A reading can still pass that is wrong and not extreme: Cleveland's 38.3 C on September 26, 2017 is one we suspect.

Dew point goes with the temperature where a report is removed, and on its own more than 20 C below its 1st percentile or as a one-hour spike [A]. Its low margin is wide because real dry air runs far from normal (Lubbock and Abilene, June 9, 2020). 1 to 7 hours a station.

Effect, same draws (40) before and after, at each station on its own: towers' water within 0.5%. Fort Worth hybrid +1.9% and assist +2.1% on average; Kimble +2.4% and +2.7%; Cotulla +0.6% and +1.1%, its hybrid peak day +4.6%; McAllen under 0.3%. Stations losing only hours move under 0.15%. Michigan's weather is ERA5, which has neither gaps nor sensor faults; the screens apply to NOAA station records wherever they are used. Each division's `screen` records what was removed.

**Local standard time.** ERA5 weather was asked for in Detroit's time zone at any place. Now UTC, moved to local standard time by longitude, the rule the station records already use, and trimmed to whole local days: `round(lon / 15)`. So Michigan's regions move from UTC-5 to UTC-6, and day boundaries move an hour. At West Michigan, 12 draws: averages within 0.01%; peak day towers -0.02%, closed loop -0.3%, assist +0.3%, hybrid -1.4%. Cached weather files are not reused, as their times differ, so a rebuild downloads Michigan's eight regions again.

**Great Lakes.** `waterledger_data.greatlakes`: the nearest Great Lake or Lake St. Clair within 5 km of a place's boundary, by distance between polygons, in every state (Census boundaries; Natural Earth 1:50m). Michigan measured between the vertices of the two outlines, which missed places on the shore: Sanilac township, 0 km, was not counted. Places on a lake: OH 85, WI 130, IN 29, IL 32, NY 90, PA 13, MN 19; MI 312 to 325 (13 gain, none lose, 7 change lake where two meet: Sault Ste. Marie from Superior to Huron, both at 0 km by this outline, tie to the first by name). TX, VA and AZ none, as expected. These states get `great_lake`, the Compact's level as far as `levels.py` applies it, and lake-source cooling (`national.climate.lake_source`, `lake.run_lake` on GLERL's daily long-term temperatures). GLERL has all five lakes. Lake Ontario is new to the model. Lake St. Clair still uses Erie's temperatures. Lake water and lake-source cooling are refused away from a shore by one rule everywhere (`scenario.check_lake`).

`Receiving.great_lakes_basin` is new: the main watershed is in HUC region 04. The Compact covers the basin, not the shore (Akron is in it, Columbus is not), and `levels.py` tests only the shore. Left for that file's owners.

**Nearest water system.** From the place's point to the edge of the sizable system's service area, in every state (`supply.nearest_sizable`). Michigan measured to the middle of a neighboring place a quarter or more covered by the system, which depends on how large that place is and ignores where the pipes stop. We use the place's point because the campus's place within it isn't known. Michigan, of 1,071 places with no system mapped: 312 change system, median distance -3.4 km, 152 gain the 10 km reach, none lose it (221 to 373). Closed loop's starting source moves to the public system at those 152. EPA's boundaries bring oddities: Armada township now finds Center Line at 0.8 km, which reads as a mapped fragment of a service area.

A system on under 5% of a place was enough in the national tier to count as there, and Michigan's data starts at 5%. Now 5% everywhere (`supply.SERVES_SHARE`) [A]. Such a system stays listed, but the place counts as having none. Starting source for towers and hybrid moves to wells at OH 433, VA 57, TX 55 places; closed loop at OH 112, VA 20, TX 25; sewer no longer assumed at OH 160, VA 32, TX 24. Michigan's shares come from 24 sampled points and the others' from areas, which is left as is.

**Sewer plants.** A plant in EPA's 2022 survey stays unless there is positive evidence it isn't a running plant, in every state (`wastewater.plants`, now Michigan's too). A terminated or missing permit is not that evidence: permits get renumbered and moved between general and individual permits. Otsego, Michigan has MI0023744 terminated and MI0060260 effective; Au Gres, Dryden, Homer, Elk Rapids and others are the same, found by ECHO's records within about 1.5 miles of the plant. Such a live permit now takes over, with its flow.

Left out [A]: records naming themselves a capital project or only a collection system (Austin's "5 Year CIP", 152 MGD; East China and Hartland Township, Michigan, "CS", whose permits are MS4 stormwater); and plants of 0.5 MGD or more whose permits are all terminated or gone from ECHO, with no live sewer permit nearby, and a live plant at least as large in the survey's city to have taken the flow (Austin's Govalle; Chesapeake-Elizabeth, Virginia Beach). The survey's city is a mailing city, so smaller plants and those naming their own township aren't asked this: Sand Lake mails from Grand Rapids, and Hamburg Township from Whitmore Lake. A record with no permit stays, as Kalkaska's and White Cloud's do. So some unbuilt or closed plants will remain, mostly in Texas, where 193 survey records have no permit. ECHO's "Expired" is not closed (Cincinnati's Mill Creek, 221 MGD).

The earlier national rule kept only plants with a live NPDES permit on ECHO's list of public plants. OH 664 to 839 plants (first plant changes at 234 places, 10 km reach at 104), VA 217 to 238 (14, 7), TX 1,059 to 1,456 (343, 229; 125 change whether a plant is within 40 km), MI 393 to 392 (26, 9, with the distance below). Michigan's distance was map units fixed at cos 45, about 5% short east to west at 42 N. Now great circle, which alone moves the first plant at 10 places and the reach at 8. At most ten plants listed everywhere.

**Option names.** The state's own power mix is `state_mix` everywhere. `mi_mix` still works in `Site(power=...)` and `est.power_plants[...]`.

**Land and golf.** National estimates fill in acres and land before as Michigan's do (`scenario.land_default`; the numbers don't change, as `comparisons.py` used the same defaults). A state with no golf figure takes GCSAA's 2020 median for its agronomic region, labeled, from the Phase III report: North Central 40.5 acre-feet a year, Northeast 29.0, Pacific 68.4, Southeast 111.1, Southwest 375.7, Transition 38.5, Upper West/Mountain 163.2; national 66.3 for Alaska and Hawaii. 325,851 gallons an acre-foot, over 365 days. The regions cross state lines, so each state takes the one holding most of it, read from the report's map [A].

**Michigan's gaps.** Downstream paths continue past the state line through the tracer: 43 reaches added, 35 with listings; 480 of 1,541 places get a longer path (Saint Joseph River through Indiana and Ohio, Lake Erie to the Niagara). USGS's county water use sits beside EGLE's. Michigan's snapshot reaches carry assessed flags.

**Labeled.** `not_covered` on a context category names what Water Ledger has no data for yet: household wells and coldwater streams outside Michigan, and state rules everywhere, as `Jurisdiction.rules` is empty in Michigan too.

**Snapshots.** JSON files are written with sorted keys. The cause of Virginia's two receiving.json files with different hashes was `_downstream` building `reaches` through a set of strings, whose order differs between Python runs.

**Tests.** `tests/test_state_end_to_end.py` runs any state from `WATERLEDGER_TEST_STATE` with nothing hand-listed and no other state's data, and build-state's check step now runs it. On the published OH, MI and TX snapshots it takes seconds.

## Nov 1, 2026: 400 draws

Each location now runs 400 Latin hypercube draws, up from 200 (`physics.DRAWS`), set by Andrew. At 200, with 12 seeds, the 95% half-width was 2-3% on towers and under 1% on PUE, but 6-16% on the hybrid and assist average medians, and 21-66% on their low ends, which are about 0.01 MGD. Error falls with the square root of the draws, so 400 should cut that noise by about 30%. It doubles the cooling compute on every build. The convergence check is to be rerun at 400 and reported here.
**Very small water systems.** The main system (`main_system`) is sometimes a very small one that covers a small part of the place, such as a mobile home park inside a township: Riverboat Bend Trailer Park at Kenefick, Texas (40 connections, 15% of the town), or a single-connection system at 0.7% of a township in Ohio. A campus as a percent of those connections reads as thousands of percent and says nothing about supply. Where the main system has under 100 connections and covers under half of the place [A], the comparison now gives no percent and says a campus would need a larger supply (`comparisons.tiny_system`). Both limits are judgment. 100 connections is roughly 300 people, inside EPA's very small class (25 to 500 people), and half is the share that already makes a system the place's main one. This applies at 75 places: 13 in Michigan, 40 in Ohio, 6 in Virginia, 16 in Texas. In 69 of them every mapped system is that small. In the other 6 a larger system is mapped at a small share of the place (Martin County, Texas: Midland at 0.9%), and the text says so, because "the only mapped systems" would be false there. A small town's own system keeps its percent, with the existing wording: Dodson, Texas has 48 connections covering 99.8% of the town. Which system is main is unchanged. A rule using connections among systems covering at least 25% was tested on all four states; it fixed Holland, Michigan and Miami Township, Ohio, but broke Kentwood, Michigan, Boones Mill and New Castle, Virginia, and Live Oak, Texas, because EPA's service areas overlap. The page names the system it uses, so a reader can see the choice.

## Nov 2, 2026: integrating model 1.7

Finishing the merged groups' work. Numbers are at 300 MW where they move at all.

**Michigan's parameter sources.** `PARAM_SOURCES` in `states/mi/build.py` now has one entry per parameter in `physics` and no others, which a test holds. Cycles cite Lei and Masanet's preprint and Han et al., with FEMP's lower typical range, two to four, stated in FEMP's citation. Loop volume cites Crusoe's post, whose text gives about 1,700,000 gallons for a typical fill; Lowell's report was cited there by mistake and stays only as a validation check. Drift adds EPA AP-42 13.4, read through secondary copies because EPA's site refuses automated requests. Load factor, the switch margin, the hybrid's offset and the maintenance terms are added; `assist_on`, `hybrid_on` and `hybrid_full` are gone. Hermantown's slides and Trane's DC-WPR004A are named in `physics.SOURCES` but have no source entry: no address for either was found, and Trane's paper was not located when we looked again today, so it rests on the audit's reading. The Uptime Institute, 2017 NRI and BMP Database entries are removed, as nothing cites them now. EVAPCO is dated as presented. USGS's county use, cited for a home's water, had no entry and has one.

**A patent citation corrected.** The switch point's comments and the section above say US 12,426,214 B1 has the customer set the threshold. The patent's text, read in full today, does not use the word customer. It describes a controller that goes to wet mode above a second threshold, in embodiments 70-95 F, for example 82 F. So it supports the bounds and the example; it doesn't say who sets them. That a setting is the operator's rests on EVAPCO and on the audit's reading of Trane. No number changes.

**Validation wording.** The towers check said the model was within LBNL's published range. At model 1.7 West Michigan's makeup is 1.42-1.81 L per IT kWh, median 1.59, against LBNL's roughly 1.75-2.75, so most of the band is below it. The reading now says so and gives the reason (decision 4). "Likely" gives way to the range across assumptions (decision 12). The home's figure has one definition in the file; EPA's 300 gallons appears only as `epa_family_gpd`, a noted comparison.

**Sensitivity script.** `docs/methods/sensitivity/sensitivity.py` raised an error on hybrid, which has no default design dry-bulb. Runs now go through `physics.for_location`. Its peak day is the package's, average load over the load factor (decision 1), with every computer at capacity as a separate output, `withdrawn_peak_full_capacity`. Its check against `cooling.daily_stats` covers both. Inputs stay independent, while the package links some parameters: Sobol' indices need independent inputs, so the indices read as each parameter's own effect. The stored CSVs are model 1.6 until the full run at release; a `--quick` run was used to check the script.

**Land default.** `scenario.land_default` is now the only copy, and it takes whether the place is incorporated. The merge had left two: `comparisons` tested `Place.incorporated`, while the national provider called `land_default(place.kind)`, which tested for `"city"`, and filled in the site before `comparisons` saw it. So the fix recorded on Nov 1 did not reach national estimates: Leesburg, Virginia, still started on 200 acres of farmland, and it now starts on 50 built, like Ohio's villages and Texas's towns. Michigan's starts don't move, since its incorporated places are all cities.

**The Compact follows the basin.** `levels.site_levels` read the Compact's 5 MGD only for a place within 5 km of a lake. The Compact covers the basin, so it now reads for a place on a lake or with `great_lakes_basin` (main watershed in HUC region 04; Akron yes, Columbus no), and `great_lakes_where` says which. The main watershed stands for the place, and it says nothing about where a water supplier's water comes from. The line is the Compact's own; no threshold is added, and no estimate moves (decision 13).

**What the weather is called.** Nov 1 corrected the models package. The same label stood in the data package, `site.estimate`, Michigan's source list and snapshot manifest, the READMEs and the briefs' script: "ERA5" for a request that names no model, so that Open-Meteo's best match applies. Its documentation says that combines ERA5, ERA5-Land and, from 2017, IFS HRES. These now say that. `weather="local"` is described as the nearest point on that record: Gaines's request answers at 42.85 N, 85.47 W. The source's id stays `era5` so links to it keep working. Dated notes (design 0001 and 0002, `national-tier-notes.md`, `station-distance-check.md`, older entries here, the changelog's past releases) stay as written, and should be read this way. ERA5 proper is the next release.

**Stable utility order.** A place's utilities in `energy.json` came from `sort_values("share")`, whose order among ties isn't stable, and ties are common: territories overlap, so several utilities can cover all of a place. A tie now goes to the lower EIA id, then the name (`energy.in_order`), in every state, cached or fresh. The order shown to a reader was already fixed by `energy.ranked`. Snapshot files keep their sorted keys through the one `_write`, which Michigan's writer shares; both are tested. No number moves.

**A second water system.** Where another system covers at least a quarter of the place, the comparison names it (`second_system`, `second_system_share`; `comparisons.second_system`). A quarter is judgment [A]; it is the share at which a campus's site is reasonably likely to fall in that system's area. The rule for the main system is unchanged, and the percent is still the main system's. Because EPA's areas overlap, two systems can cover the same ground, and the field says only that the system is mapped there. It is a way to show a reader the choice that the main-system rule makes, as with Kentwood and Holland above.

**Blowdown's cycles.** `runoff.PARAMS["blowdown"]` still had 3, 5 and 7 cycles when the cooling model went to 3-6 (decision 2). It now has 3, 4.5 and 6, held to the cooling model by a test. On lake makeup, dissolved solids go from 510 / 850 / 1,190 mg/L to 510 / 765 / 1,020; on groundwater, from 1,200 / 2,000 / 2,800 to 1,200 / 1,800 / 2,400. Makeup's 170 and 400 mg/L have no source and are now marked [A]. Only Northline's screen and Michigan's pages read this; no state's estimate does.

**Michigan leftovers, searched.** We searched the packages for Michigan, MI, Detroit, EGLE, Part 327, America/, mi_mix, Great Lakes and the state's place names, then read each hit in shared code. No Michigan value was found reaching another state's number. Stated now: the Michigan rule values in `runoff.PARAMS` (construction permits, Rule 57's chloride, the coldwater limit, Rule 60's phosphorus limit) are marked as Michigan's, and no calculation reads them. Staff and maintenance water's share lost comes from a coefficient for the Great Lakes Basin and climatically similar areas; using it in Texas is an assumption [A], and at 300 MW all of that water is about 7,000 gallons a day, of which about 900 is lost. Left on purpose: `levels.PERMIT_NOTES` and `scenario.septic_rule` are Michigan's and read only where rules are reviewed or by Northline's text; `POWER_ALIASES` keeps `mi_mix` working because the published Michigan data and the site still use that name; `waterledger_data.power`, `waters` and `places` are Michigan's builders, with national callers using only their state-neutral helpers. Shared comments that name Michigan as history or as an example stay.

**Convergence at 400.** The check from Nov 1, at `physics.DRAWS`: 12 seeds, Gaines and Houston, cooling water alone at 300 MW; 95% half-width of each percentile as 2 standard deviations across seeds, Gaines then Houston.

| Output | p10 | p50 | p90 |
|---|---|---|---|
| Towers withdrawn, average | 1.9, 2.4% | 1.1, 1.3% | 1.9, 2.0% |
| Towers consumed, average | 1.6, 1.8% | 1.1, 1.3% | 1.4, 1.6% |
| Towers withdrawn, peak day | 2.6, 2.8% | 1.3, 1.2% | 1.7, 1.5% |
| Annual PUE, all designs | 0.2-0.5% | 0.4-0.5% | 0.5-0.9% |
| Hybrid withdrawn, average | 42, 16% | 10, 5.7% | 4.3, 4.5% |
| Hybrid consumed, average | 43, 18% | 8.4, 6.4% | 2.7, 3.3% |
| Hybrid withdrawn, peak day | 9.6, 3.9% | 2.1, 1.5% | 3.5, 3.6% |
| Assist withdrawn, average | 42, 18% | 9.1, 5.1% | 6.6, 5.3% |
| Assist consumed, average | 40, 17% | 12, 5.2% | 5.6, 5.6% |
| Assist withdrawn, peak day | 11, 5.6% | 3.8, 2.4% | 4.4, 4.2% |
| Closed loop, cooling water, average | 8.3, 6.9% | 5.5, 4.1% | 3.1, 4.0% |

Towers and PUE meet 1-2% at the median and upper end, with towers' low end a little over on the peak day. Hybrid and assist do not: their average day medians are good to 5-12%, their upper ends and peak-day medians to 2-7%, and their low ends not at all in a cool climate. Against one run of 1,000 draws, the mean of the 12 seeds runs +15% (hybrid) and +22% (assist) at Gaines's low end, about 0.01 MGD, and within 1.5% at the medians. So those low ends should read as near zero, and more draws won't soon change that: going from 200 to 400 moved Gaines's hybrid median from about 11% to 10%. A few interacting parameters set that tail.

Closed loop's headline is nearly all staff water, and that is the weaker number here. Staff water stays on plain uniform draws, which are not a hypercube: 8.5, 4.8 and 3.9% at p10, p50 and p90 across 12 seeds. Seed 13's median at 400 is 6,646 gallons a day against 6,888 over 100,000, 3.5% low, so 300 MW of closed loop reads 6,900 where about 7,150 is the long-run figure. Moving staff water to the same sampler would likely close most of this. It changes published numbers and needs a decision, so it hasn't been done. DRAWS stays at 400.

**The wider withdrawal error, checked.** Nov 1 raised the shared error on Macknick-filled withdrawal from 0.35 to 0.81. `reconcile.py` could not be rerun, as it needs EIA-930's files, which aren't in the work folder; its r values compare Siddik et al. with raw reports, as noted then. The effect was worked from `state_power_water_combined_2024.csv`, undoing the term. L per kWh, statistical range with 0.81, then with 0.35: Texas (13.0, 60% of its water filled) 4.6-37.3, 7.2-23.7; Virginia (30.8, 12%) 19.3-49.2, 19.9-47.7; Ohio and Michigan (1%) unchanged. So this is a Texas matter. Before the water body review, Texas stood at 19.2, 11.8-31.2.

The wider range is the more honest one, for three reasons. The filled plants' reports are mostly circulation, median 54,000 gal/MWh over the 25,000 line, and Macknick's medians of 5,950-12,225 sit between that and the 500-700 of make-up alone, so the error is one of definition and is shared across plants. Treating plants as independent would give 0.14 for Texas against 0.49 as shared, and that would hide it. The value isn't high for the plants in question either: Macknick's coal pond range, 300-24,000, gives 1.11, and coal and gas steam are 43% of Texas's water against nuclear's 14%. A test of the ends, from Texas's plants: with the filled plants at what they consume, Texas is 5.5, and 4.6 falls a little below that, a limit of a symmetric lognormal. With those plants as reported, circulation included, it is 49, near Siddik et al.'s 55 for ERCOT, and that lies above the range on purpose (decision 9).

**Which reservoirs count.** All 69 rows of `cooling_water_bodies.csv` were read. In the four states the classes hold: Texas's are off-channel or built cooling lakes, North Anna is the only one in Virginia, and Sabine, Cedar Bayou and Barney Davis stay once-through and saline. The main-stem exclusions (Sequoyah, Peach Bottom, Arkansas Nuclear One, Cooper) are plants small against large rivers. Two readings outside the four states are weaker: G G Allen on Lake Wylie is once-through as small against the Catawba, while McGuire and Marshall just upstream on Lake Norman are reservoirs, and the test is still a reading, not a computed flow ratio [A]; Coughlin's Bayou Cocodrie is called a built reservoir on EIA's fields alone. Both should be checked before those states are published.

**Sewer plants added, checked.** Texas's 1,059 to 1,456 and Ohio's 664 to 839 are from the sewer plant rule, not the power work. Of what is now listed but not on ECHO's live list of public plants (321 in Texas, 137 in Ohio; that list's count differs a little from the earlier rule's): most are small, 249 of Texas's under 0.5 MGD and 124 of Ohio's, and they hold 5.2% and 1.1% of design flow. The largest are running plants as far as we can tell from their names, not from a check of each: Midland's, San Angelo's sewer farm, Fort Bliss's Fred Hervey, Summit County's Fish Creek. Eleven in Texas and two in Ohio sit within 300 m of another record, a few of which look like one plant twice or a bad coordinate. In Texas 298 of the 321 have no reported flow, so there's no spare room to compare with.

**Staff water on the Latin hypercube (Nov 2, 2026).** Staff and maintenance parameters were the one set still on plain uniform draws, and they are nearly all of closed loop's headline. At 400 draws and the fixed seed the 300 MW median read 6,646 gal/day against a long-run 6,897 (3.5% low); 40 seeds gave 2 SD half-widths of about 8.5, 4.8 and 3.9% at p10, p50 and p90. `physics.sample_staff` now uses `latin_hypercube` on its own stream, and `cooling.staff_runs` reads the same draws. At 400 draws: 4.7, 2.1 and 3.0%, with the fixed seed at 6,900. Ranges are unchanged. Draws are no longer nested: 50 draws are not the first 50 of 200.

**Gaines per-building figure (Nov 2, 2026).** The source linked for Microsoft's "about 2,000 gallons a day per building" was a WOOD TV article on the noise study, which doesn't contain the figure. Our earlier notes disagree on its origin: this log said Microsoft's Tyrone letter, and Northline's records say Jonah Mills of Microsoft per Sun and News, Apr 25, 2026. A search on Nov 2 did not find the article. The link is removed and the citation says it is not re-verified. The validation row stays, labeled, until a primary copy is read.


## Nov 2, 2026: nitrogen in the before and after

Nitrogen joins sediment and phosphorus in `before_after`: rows `n` and `n_no_controls`, typical wet ponds and no controls, read from `runoff.loads` as the others are. The loads aren't new, only the rows. Farmland's nitrogen today counts surface runoff only (TN 1.9 mg/L, STEPL, unread), with tile-drain nitrate left out, so a campus's change against farmland reads too high until the method by land cover is settled. The pages say so.

Pollution loads rest on general national and state values, not on a site's soils, slopes, drainage or practices, so a site study can move them a lot. The pages say that beside the loads.

## Nov 2, 2026: phosphorus and nitrogen by land cover

Short: each land cover reports what leaves an acre in a year. Developed land and the campus are Simple Method runoff x one whole-site concentration (NSQD 4.02), plus the natural yield on the pervious share [A]. Farm fields are USDA CEAP II's loss per acre by production region. Natural land is Clark et al. 2000's measured basin yield. Ponds treat the surface part down to an effluent floor. A site study can move all of this a lot, and the pages say so.

Why. Runoff x concentration on every cover gave farmland and the campus with ponds the same phosphorus in every state, from fixed constants. Natural land carried about 0.9 in of runoff and half its load came from its 1% impervious share, while its nutrients travel mostly as baseflow. Pavement took outfall concentrations, which already hold roofs and landscaping, with turf added separately.

Rejected, on purpose. Ecoregion yields by place (Smith, Alexander and Schwarz 2003, Fig. 3): the values only exist off a log-axis chart here, its supplement was unreadable, and natural land is so small against the others that it moves "about 20 times" to "about 15 times", not an answer. CEAP regions by place: CEAP publishes no boundaries, and digitizing Fig. 2 adds error we couldn't defend. Rain-zone concentrations: real, but thin and not monotone across zones (non-residential TP means from the data file: RZ1 0.26, RZ2 0.34, RZ5 0.43; 16-23 sites in several). A simple method with stated limits holds up better than a detailed one with holes.

Whole-site concentrations. Means from NSQD 4.02's brief (Pitt, Maestre and Clary 2018): institutional, commercial and industrial as low, middle, high [A]: TP 0.20, 0.31, 0.40; TN 1.9, 2.7, 3.1. Reproduced from the data file with non-detects at half the limit, within 4%: TP 0.198, 0.320, 0.412; TN 1.73, 2.81, 2.83. TSS from the file: commercial 118, institutional 144 (13 sites), industrial 152; 118 is the middle, with v1.1's commercial 96 low. Concentration does not fall with imperviousness in the file (site means, r = -0.25 for TP), so one value at 50% is fair; sites near 50% are few. Built land takes the same values, so a campus on built land changes by impervious share, not a choice of class [A]. Against the old flow-weighted campus (TP 0.34, TN 2.82) the middle moves little.

Farmland. CEAP II, Conservation Practices on Cultivated Cropland (2022), tons in Tables A-17 to A-20 over acres in A-1: modeled (APEX) area means at the field's edge, 2013-16 practices, surface and below ground. Low: the mean on acres meeting CEAP's thresholds. High: the mean on acres over the dominant pathway's threshold plus the other pathway's mean. Low and high show the spread between fields [A], and the high runs well above measured quartiles. A state takes the region holding most of its cropland, read from Fig. 2 [A]: MI and OH North Central, VA East Central, TX Southern and Central Plains; other states the national row until each is added. Virginia's Coastal Plain (2.21 lb TP) and Texas's Gulf Coast (2.69) differ from these, inside the ranges.

Check against measurement, MANAGE v5 (2018), our selection of row crops, excluding grass, pasture, hay, silage, citrus, potato, sugar and vegetables, lb/ac/yr. Below-ground nitrogen, tile drains, NCM states (MI, OH, IN, IL, WI, MN, IA, MO), n = 850: median 20.5, mean 24.5, against CEAP's 24.6, though MANAGE's sites are all drained and CEAP's acres aren't. Surface phosphorus, same states, n = 35: median 0.98, mean 2.82; drain phosphorus, n = 127: median 0.04, mean 0.15; CEAP's 2.07 total sits between the summed median and mean. Texas surface phosphorus, n = 38: median 0.89, mean 1.35, against the Southern and Central Plains' 0.99. Surface nitrogen in Texas, n = 31: mean 9.9, CEAP's total 16.3, surface 6.4. Virginia has no MANAGE records, and the East has almost none; Chesapeake Phase 6 adopts 38.2 TN and 1.87 TP against East Central's 44.7 and 3.86, so Virginia's phosphorus may run high. Experiments favor erosive, fertilized plots, so measured means may run high too.

Natural land. Clark, Mueller and Mast 2000, Table 1, 63 undeveloped basins: median basin yield 8.5 kg/km2 TP and 86 TN, quartiles as lb/ac 0.043, 0.076, 0.107 and 0.40, 0.77, 1.96. MANAGE's forest controls: TP median 0.07 (n = 10), TN 1.18 (n = 14). Chesapeake true forest: 0.08, 1.68. Keeps Rv 0.03 for the runoff row only. Weakness: a basin yield has in-stream loss, and the Southern Plains and Corn Belt are poorly represented; dry West Texas runs lower (Welder Refuge TN 0.21 lb/ac).

Below the campus. The natural yield on the pervious share stands in for what passes below lawn and landscaping [A]. No campus has been measured. Fertilized turf would run higher: Region 1's developed pervious is 0.12 lb TP and 1.2 TN on soil group B, Chesapeake's turf 0.83 and 11.2.

Controls. Wet ponds: CWP 2007 Table 2, TP 0.39, 0.52, 0.76, TN 0.16, 0.31, 0.41 (quartiles and median), replacing SEMCOG's 0.51 and 0.33; sediment stays 80%. Floors from median effluent in the 2012 BMP Database summary, Table 11: TP 0.13, TN 1.1 (TKN alone, as that report has no pond TN). Pulling the 2020 summary is open. Infiltration: the old code took 70% and 51% total removal on top of a 50% volume loss, reaching 85% and 75.5%. Now runoff reduction and removal are apart (Runoff Reduction memo Tables 2-3, 7): volume 0.5, 0.7, 0.9 ([A] for the middle), removal 25% and 15%, sediment 80%, about SEMCOG's 95% in all. Nitrogen soaked in is reported as gone to groundwater (`to_ground`), so the balance closes.

Comparison across covers. Field edge, outfall and basin are different scales; below-ground nitrogen on farmland includes deep percolation, some of which never reaches a stream. Against a campus, Lansing's farm nitrogen is 1,145 lb surface and 6,060 in all, on either side of the campus's 2,370, so the package keeps surface apart (`now_surface`) and the detailed page gives both.

Open. Phosphorus carried by construction sediment isn't counted: 4,000 tons at 0.04-0.08% is about 3,200-6,400 lb a year, and it needs a sourced soil fraction. CEAP's Rv implied in the Great Lakes (about 0.15) against farm 0.20 [A], which drives the runoff row only now.

## Nov 2, 2026: pollution out of the before and after

Sediment, phosphorus and nitrogen leave `before_after` for `est.site_loads`. They cover the change in runoff from the finished site, which is not the change the project makes, and a "less" beside water and electricity reads as "less pollution". On farmland, with working ponds, runoff nutrients probably do fall: fertilizer stops. But construction, cooling water and stream bank erosion can outweigh that, and a site study can move all of it.

`site_loads` also has what can be numbered. Phosphorus in construction sediment: `construction_p`, sediment x 0.04, 0.06, 0.08% by weight [A]. The high end is what CEAP implies for sediment leaving North Central fields (1.49 lb on 0.96 tons an acre), fertilized and enriched by sorting, so probably high for graded subsoil. USGS's soil surveys (Shacklette and Boerngen 1984; Smith et al. 2014) should replace the low end; neither could be read yet. Phosphorus in cooling wastewater: `cooling_p`, flow x 0, 3, 6.5 mg/L of inhibitor phosphorus, and what a plant at 1 mg/L passes. Stream bank erosion has no number: one simple figure would be worse than saying it isn't counted.
