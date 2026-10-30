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

## Open

- Station distance: how far places are from their division's station, and how much a nearer station changes the
  estimates ([station-distance-check.md](station-distance-check.md), in progress).
- NOAA climate division names in the data.
- Virginia's withdrawals by use type (published only in DEQ's dashboard; a bulk export to request).
- The share of homes a utility serves, shown for Michigan, needs a national source.
- Michigan's move to the shared format (design 0003, decision 8), with its home electricity figure.
- Byte-identical snapshot rebuilds.
