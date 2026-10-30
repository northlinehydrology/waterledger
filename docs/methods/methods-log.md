# Methods log

A dated record of method decisions: what was decided, why, what else was considered, and what is still open. It is the
long form. The short forms are the two-page briefs (`docs/methods/<st>.pdf`) and the methods pages on waterledger.org
(`/methods/`, `/methods/<st>/`, Michigan's `/mi/methods.html`), and they are kept in step with this log.

Layer-by-layer notes for the national tier (places, water supply, wastewater, receiving waters, climate, energy) are in
[national-tier-notes.md](national-tier-notes.md); county water use sources are in [water-use-sources.md](water-use-sources.md).
This log covers decisions that cut across layers, and points there for detail.

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

**Short form (methods pages, briefs).** Electricity: the computers are taken to draw 50 to 80% of their capacity on
average (EPRI 2026 measurements; IEA 2025), plus cooling and power losses by design (LBNL 2024; checked against
Google's and IEA's reported PUE). Power plants: Michigan's mix uses up about 0.9 L of water per kWh (0.6 to 1.2) and
draws about 57 L (50 to 61), 98 to 99% returned warmer (EIA plant reports for 2024, EGLE, Macknick et al. 2012).
People on site: 20 to 60 plus 0.1 to 0.5 per MW (JLARC 2024; announced campuses), each using 10 to 30 gallons a day
(EPA 2002; Michigan's septic design criteria), about 10% used up (USGS).

## Open

- Model 1.3 is on the branch `defensible-parameters`, not released. Release steps: rebuild Michigan's site data and
  snapshot, refresh `tests/data/water_ledger_west_michigan.json` (per_100mw) from the published estimates, add the
  methods-page changelog entry for 1.3, and put the short form above on the methods pages and in the briefs.
- The remaining parameters marked [estimate] in `physics.py` (economizer and chiller heat factors and wet-bulb
  thresholds, assist and hybrid temperatures and shares, closed-loop volume per MW) need the same check.
- National-tier states' power-plant water (`waterledger_data.energy`) needs the same plant-data check as Michigan's.
- A maintenance and washdown term for applicant comparisons, separate from staff water.
- Station distance: how far places are from their division's station, and how much a nearer station changes the
  estimates ([station-distance-check.md](station-distance-check.md), in progress).
- NOAA climate division names in the data.
- Virginia's withdrawals by use type (published only in DEQ's dashboard; a bulk export to request).
- The share of homes a utility serves, shown for Michigan, needs a national source.
- Michigan's move to the shared format (design 0003, decision 8), with its home electricity figure.
- Byte-identical snapshot rebuilds.
