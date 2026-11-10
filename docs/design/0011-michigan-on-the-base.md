# 0011: Michigan on the base path: every state is the base plus its own layers

Status: **proposed, Nov 9, 2026, for review. No code yet.** Comes before 0010's refactor, as its own release, so that
0010 has one path to move onto and its decision 5 needs no Michigan exception. Cathode materials plants move to 0012.

## Why

Michigan came first, and the national tier was built around it rather than under it (Andrew, Nov 9: "mostly I think
it's an artifact of the decision that it came first"). Today:

| | Michigan | Ohio, Virginia, Texas, Wisconsin |
|---|---|---|
| Built by | `states/mi/build.py`, which writes the site files first | `national/build.py`, which writes a snapshot |
| Snapshot | written *from* the site files, which it carries in `michigan/` | the source |
| Site files | copied out of the snapshot (`engine/products/mi_data.py`) | written from the snapshot (`engine/products/state_data.py`) |
| Package answers | `states/mi/provider.py`, reading the site files through `scenario.py` (map coordinates, short keys) | `national/provider.py`, reading the snapshot |
| Page | no `state` block in `estimates.json`, so `wq.js` falls back to "Michigan" | a `state` block |

The page is already shared: every state's page is Michigan's, and every state runs the same `wq.js`. The cooling
numbers are already shared too: since model 1.8 every state, Michigan included, uses ERA5 cells with the same staff,
lake and grid-water results. The split is in how the place data is built and read.

What Andrew wants (Nov 9): **the base state plus more, not a separate process, and no better estimate lost.** Michigan
has denser local data (EGLE's reported withdrawals, Wellogic wells, DNR trout streams, MPSC territories, reviewed state
rules). That data stays. It becomes layers on top of the base that any state can have.

## The rule: base plus layers

Every state is built by one builder. For each category of place data, the national source is the base. A state can add
its own layer, and a layer does one of two things:

- **adds** something the base doesn't have (household wells, trout streams, state rules), or
- **replaces** the base for that state, where the state's own source is better (reported withdrawals in place of USGS's
  2015 estimates).

County water use already works this way: `wateruse.state_layer(state)` replaces USGS's estimates with Ohio's, Texas's
and Virginia's own records, and `write_water_use(state_layer=)` passes Michigan's EGLE layer in. This note uses the same
pattern for every category. A layer lives in `waterledger_data` with the state's other sources, is registered by state
and category, and is recorded in the snapshot's manifest (`layers`: category, source, adds or replaces). The provider
reads the layers wherever a snapshot has them; nothing in the provider asks which state it is.

**When a layer replaces the base** depends on what it is:

- **The state's own records** (a regulator's reports, maps or rules: EGLE, MPSC, Wellogic, DNR) are kept unless they
  measure worse than the base. The people who use a Michigan study (township boards, reviewers, utilities) know and cite
  these sources, so they carry weight beyond their error rate (Andrew, Nov 9).
- **Our own constructs** (groupings, default rules) are compared with the base against an independent check, and the
  better one is used.
- **Close averages do not make two sources interchangeable** (Andrew, Nov 9). A comparison reports where the two
  differ, place by place, and which is closer there; a tie on average with large local differences is decided area by
  area, not by default.

Each replacement is stated in the methods page with its reason and the comparison.

This is the add-state process in two passes (Andrew, Nov 9: "a nation flavor first addition. And a later second
addition that deep dives on state level data"). A state first goes on with the national base alone. A later deep dive
adds its own layers one at a time, each kept only where it measures better. Michigan is a state whose deep dive was
done first; moving it onto the base keeps the layers that earn their place.

## Michigan, category by category

From the code as of Nov 9. "Compare" means the numbers are measured side by side before choosing (step 1 below).

| Category | Michigan today | National base | Plan |
|---|---|---|---|
| Places | 1,541 cities and townships (county subdivision GEOIDs) | Census places, county subdivisions and counties | Keep Michigan's list and GEOIDs (see "Places"); villages are a later question |
| Water systems, nearest sizable system | EPA service areas, the shared rule | the same | Base |
| Sewer plants | `wastewater.plants("MI")`, the shared rule, at map coordinates (about 200 m) | the same, at true positions | Base (true distances) |
| Watersheds, downstream path, impairments | USGS WBD; ATTAINS, Michigan's 2026 report | USGS WBD; ATTAINS by HUC12 | Compare (same sources; check the cycle) |
| Trout streams | Michigan DNR | none | Layer (adds) |
| Household wells | EGLE Wellogic | none | Layer (adds) |
| County water use | EGLE reported withdrawals, 2025 | USGS 2015, or a state layer | Layer (replaces), moved into `wateruse.STATE_LAYERS` beside Ohio, Texas and Virginia |
| Design storms | NOAA Atlas 14 | the same | Base |
| County rainfall | NOAA Climate at a Glance by county | the same source | Compare |
| Cooling weather | ERA5 cells | the same | Base (already shared) |
| Road salt regions | Michigan's eight regions, stations chosen by hand, salt days by the national method | NOAA climate divisions (ten in Michigan), their ISD stations | Layer (replaces), with the eastern Upper Peninsula split off; decision 3 (measured below) |
| Golf course water | median of 453 EGLE-reported courses, 43,500 gal/day | GCSAA's North Central survey median, 36,200 gal/day (no Michigan entry in `wateruse.GOLF`) | Layer (replaces): reported beats a survey; measured below |
| Electric utilities | MPSC service territories | HIFLD territories (PNNL's copy) | Layer (replaces): measured below; the base also gains an EIA-861 county screen in every state |
| Balancing authority | a hand-kept list of Michigan's PJM utilities | HIFLD control area, then EIA-861 | Base, if it gives the same seven utilities (the list's comment says it came from these sources) |
| State rules | reviewed: Part 327, Part 22 septic, the Compact | not covered | Layer (adds) |
| Source citations | `states/mi/build.py`'s `SOURCES`, which `state_data.py` also imports | | Moved to a shared module; no change in content |

## Measured, Nov 9

Scripts and output: the session scratchpad (`mi/utilities.py`, `mi/salt.py`), from Michigan's 2026-11-09 snapshot.

**Utilities.** Judged against EIA-861's Service Territory file (2025), where each utility lists the counties it serves:

| | Top utility serves the place's county | Same top utility as MPSC |
|---|---|---|
| MPSC | 1,540 of 1,540 | |
| HIFLD, ranked by customers (the base) | 1,062 of 1,541 | 819 |
| HIFLD with an EIA-861 county screen | | 1,072 |

HIFLD draws territories coarsely, and the base ranks a place's utilities by customers, so DTE comes first in 280
Consumers Energy places and dozens in the Upper Peninsula. The balancing authority, which sets power-plant water,
differs in 21 southwest Michigan places (Indiana Michigan Power and Midwest Energy Cooperative, in PJM). MPSC replaces
the base in Michigan. The county screen goes into the base for every state (fix all states): the top utility misses
EIA's county list in 5% of Ohio's places, 2% of Virginia's and Texas's and under 1% of Wisconsin's; screened, the grid
region changes in 8 Texas places and none elsewhere.

**Road salt.** Median winter days with precipitation at 1 C or below, 2005-2024 (NOAA ISD-Lite), the measure
`runoff.salt_events` uses (0.6 events a day). Checked at the ten Michigan stations with whole records that neither
grouping uses: mean absolute error 10.8 days for the eight regions (bias +6.6), 9.1 for the divisions (+4.5). At the 810
places within 40 km of a station: 4.4 and 4.8 days. Close on average, but not interchangeable: the two differ by 5 days
or more at 539 of the 1,541 places, and by 20 to 30 days at 88. Area by area, against the nearest stations:

| Where they differ | Places | Regions | Divisions | Nearest observed | Closer |
|---|---|---|---|---|---|
| Eastern Upper Peninsula | 38 | 119 | 93 | Chatham 82 (36 km) | Divisions |
| Northeast region in the eastern UP division | 17 | 88 | 93 | Sault Ste. Marie 101 (24 km) | Divisions |
| Southwest region in division 8 | 121 | 64 | 72 | Kellogg 63 (65 km), South Bend 60 | Regions |
| Central region in division 9 | 107 | 71 | 62 | Lansing 71 (15 km) | Regions |
| West region in division 9 | 36 | 72 | 62 | Grand Rapids 72 (30 km) | Regions |
| West region in division 5 | 68 | 72 | 67 | Muskegon 67 (38 km) | Divisions |
| Thumb region in division 10 | 49 | 64 | 59 | Flint 64 (22 km) | Regions |
| North region in division 6 | 18 | 89 | 64 | Roscommon 96 (67 km) | Regions |
| North region in division 5 | 32 | 89 | 67 | Muskegon 67 (91 km), Traverse City 89 (93 km) | Unclear |

The regions are closer for more places; their one large miss is the Upper Peninsula, which they give a single station
(Hancock, 119 days). So Michigan keeps its regions as a layer, with the eastern Upper Peninsula split off on its own
station (decision 3). A place's own nearest station was tried and did not do better (10.7 days at all 32 stations,
each predicted from the others); the station network is too thin for the lake-effect gradients. The per-place answer
for every state is the place's own ERA5 cell, corrected to stations as cooling weather already is, once the cells'
precipitation is pulled (later). The base gets NOAA's own division names ("Southwest Lower") in every state, in place of
"MI climate division 8".

**Golf.** EGLE's reported median (453 courses with a usable report) against GCSAA's survey figure. Splitting the
median by region or division doesn't help: predicting each course from the others misses by about a factor of two
whichever grouping is used (median absolute log error 0.81 to 0.85). So the statewide reported median stays, as a
layer like Ohio's ODNR figure.

## No better estimate lost: the check

Step 1 writes every number the Michigan page and `wl.place(...).estimate()` show, for all 1,541 places, at the starting
settings and every cooling design, from today's path. After the switch, the same numbers again. Every difference
gets a cause:

- **expected**: the base or a layer is better (true distances in place of map coordinates, a newer source);
- **bug**: a better Michigan source was dropped or read wrong. These are fixed before release.

Andrew reviews the list of differences and their causes before anything is released or deployed. A default rule that
flips at the 10 km line, because a distance moved by 200 m, is listed by place. The methods log records the data
change, and Michigan's model version is unchanged (no model changes).

## Places

Michigan's GEOIDs are public API: `wl.place("2608130860")` and every saved scenario use them. They stay. The base
builder gains a state places rule (which Census layers make a state's places), and Michigan's rule keeps cities and
townships as county subdivisions, as now. Adding villages, or counties, is a separate question for later.

## The 3.x promise

- `waterledger.scenario`'s Michigan readers (`data`, `place`, `find`, `scenario`, `src_for`, `dest_for`, ...) and
  `waterledger.states.mi` keep working through 3.x with a `DeprecationWarning` and a CHANGELOG **Deprecated** entry.
  The shared functions in `scenario.py` (`cooling_estimate`, `lake_estimate`, `check_lake`, `land_default`,
  `for_plant`, `electricity`, `grid_water`) stay where they are.
- `wl.place`, `Place`, `Context` and `Estimate` keep their shape for Michigan. Fields Michigan alone fills
  (`household_wells`, `coldwater_streams`) are filled from the layers.
- Older packages (3.15 and earlier) read Michigan through the site files. They fall back to waterledger.org/mi/data/
  when a snapshot has no `michigan/` folder, so new snapshots can drop the folder as long as the site files keep their
  shape. A test reads the new site files with 3.15's `scenario.py`.
- Snapshots already published are not changed.

## The site

`state_data.py` writes Michigan's files like every other state's, and `mi_data.py` is retired. Michigan's
`estimates.json` gains a `state` block listing its layers, so the "no block means Michigan" fallback in `wq.js` can go.
The page's rule text for Michigan (Part 327, the septic thresholds) stays in `wq.js` as Michigan's rules for now;
turning rules into data waits until a second state's rules are reviewed. The page change is small, but it changes live
numbers, so Andrew checks it locally before any deploy.

## Not in this note

- The water user contract (0010), which follows on top of this.
- Rules as data, villages, and Michigan's learn, changelog and tracker pages (unchanged).

## Order of work, each step its own commit

1. The before record: every Michigan number from today's path, for all places and designs, and the context fields.
2. Layers in `waterledger_data`: Michigan's wells, trout streams, MPSC utilities, golf median and rules flag,
   registered by state and category; EGLE moved into `wateruse.STATE_LAYERS`. The citation list moved to a shared
   module. In the base: the EIA-861 county screen and NOAA's division names, for every state (these change other
   states' context, recorded in the methods log).
3. The base builder reads layers and writes them into the snapshot, with the manifest's `layers`; the state places
   rule; `build-state MI` runs it.
4. The national provider reads layers; Michigan uses it. The old readers warn.
5. The after record and the list of differences with causes, for Andrew.
6. Northline: `state_data.py` writes Michigan; `mi_data.py` retired; `wq.js` fallback removed; parity checks.
7. READMEs, CHANGELOG, methods log; a release (3.16.0) and a Michigan snapshot, each on Andrew's word. 0010 and battery
   plants follow as 3.17.0.

## Decisions to agree

1. **Base plus layers, one builder.** Each layer adds or replaces, and replaces only with a stated reason.
2. **No better estimate lost:** the before and after record, every difference with a cause, Andrew's review before
   release.
3. **Michigan's regions stay as a layer, with the eastern Upper Peninsula split off** (its own station, Sault Ste.
   Marie or Pellston, chosen by the same check). Close to the divisions on average, but closer at more places, and the
   names are Michigan's. The split changes salt days at about 40 places, a correction recorded in the methods log.
   Later, for every state: salt from each place's corrected ERA5 cell.
4. **MPSC replaces HIFLD in Michigan** (measured: 1,540 of 1,540 against 1,062), and the base gains the EIA-861
   county screen in every state. EGLE's golf median replaces the survey.
5. **Michigan's places and GEOIDs stay**; villages later.
6. **Order:** this first as 3.16.0, then 0010 and battery plants as 3.17.0.
