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

**A layer replaces the base only with a reason**: the state's source is primary (the regulator's own records), more
recent, or measured where the base is estimated. Where the two are equally good, the base is used, so there is one
process. Each replacement is stated in the methods page with its reason.

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
| Road salt and golf regions | Michigan's eight regions, stations chosen by hand, salt days by the national method | NOAA climate divisions (ten in Michigan), their ISD stations | Compare; decision 3 |
| Golf course water | median of EGLE-reported courses | `wateruse.golf`: reported where the state reports, else GCSAA | Base (it already takes Michigan's reported median) |
| Electric utilities | MPSC service territories | HIFLD territories (PNNL's copy) | Layer (replaces): the commission's own map; compare first |
| Balancing authority | a hand-kept list of Michigan's PJM utilities | HIFLD control area, then EIA-861 | Base, if it gives the same seven utilities (the list's comment says it came from these sources) |
| State rules | reviewed: Part 327, Part 22 septic, the Compact | not covered | Layer (adds) |
| Source citations | `states/mi/build.py`'s `SOURCES`, which `state_data.py` also imports | | Moved to a shared module; no change in content |

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
2. Layers in `waterledger_data`: Michigan's wells, trout streams, MPSC utilities and rules flag, registered by state
   and category; EGLE moved into `wateruse.STATE_LAYERS`. The citation list moved to a shared module.
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
3. **Michigan's eight regions or NOAA's ten divisions** for road salt, golf and the region names on the page. My lean:
   compare, then keep the eight as a Michigan layer only if their numbers are better; otherwise use the base. The names
   ("West Michigan") show on the page, so this is visible either way.
4. **MPSC replaces HIFLD in Michigan**, after the comparison, as the commission's own map.
5. **Michigan's places and GEOIDs stay**; villages later.
6. **Order:** this first as 3.16.0, then 0010 and battery plants as 3.17.0.
