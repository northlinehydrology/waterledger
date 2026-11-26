# 0011: Michigan on the base path: every state is the base plus its own layers

Status: **proposed Nov 9, 2026; refreshed Nov 25, 2026; decisions agreed Nov 25, 2026 (Andrew: "Agreed, start 0011"). Building.** The
refresh checks the note against the package as of 3.27.0 (about 290 commits since Nov 9), marks what has been done
since, re-runs the Nov 9 measurements on Michigan's 2026-11-17 snapshot, and sets the order of work from here. The
decisions below were proposed on Nov 9 and never agreed; decision 3 changes with the new measurements, and decisions 5,
8 and 9 are new.

Where it sits: it is the next package work in Northline's plan for reports in every state (step 3b there), after the
reports read only `wl.place`, `place.context()` and `site.estimate()`, so a change in how Michigan is built reaches them
only through those calls. 0010's decision 5 (providers supply the place, facilities compute) waits on this note.

## Why

Michigan came first, and the national tier was built around it rather than under it (Andrew, Nov 9: "mostly I think
it's an artifact of the decision that it came first"; Nov 25: "it's just going to keep coming up"). Michigan has
denser local data (EGLE's reported withdrawals, Wellogic wells, DNR trout streams, MPSC territories). That data stays.
It becomes layers on top of the base that any state can have, and Michigan is built and read like the other eleven
states.

### Today (Nov 25, 2026: waterledger 3.27.0, Michigan's snapshot 2026-11-17)

| | Michigan | The other eleven states (OH VA TX WI IN MN PA GA IL NY AZ) |
|---|---|---|
| Built by | `states/mi/build.py` (`fetch.py`, `egle.py`), which writes the site files first (`waterledger build mi`) | `national/build.py` (`waterledger build-state <ST>`) |
| Snapshot | `states/mi/snapshot.py`, written *from* the site files, which it carries in `michigan/` | `national/snapshot.py`, from the sources |
| Commands and workflow | `cli.py` branches to `states.mi` for `snapshot MI` and `build mi`; `build-state.yml` has a Michigan branch (`test_snapshot_michigan.py`, a stub `MI_build.json`); `national/build.check_snapshot` loads `michigan/` into `scenario`'s cache | one path |
| Package answers | `states/mi/provider.py`, reading the site files through `scenario.py` (map coordinates, short keys); `states.Provider` sends each call to it first | `national/provider.py`, reading the snapshot |
| Facilities | `DataCenter.results` asks the state's provider; the battery cell plant already uses the national place rules (`default_source`, `default_wastewater`) | the same |
| Grid regions of ERA5 cells | `national/era5.cell_bas` gives every Michigan cell both MISO and PJM | from each place's utilities in the snapshot |
| Site files (Northline) | copied out of the snapshot (`engine/products/mi_data.py`); `engine/states.toml` marks Michigan `source = "michigan"`; `state_data.py` imports `SOURCES`, `SHORT`, `PARAM_SOURCES`, `CONTEXT`, `GREAT_LAKE_BY_HUC4` and `_dp` from `states/mi/build.py` | written from the snapshot (`engine/products/state_data.py`) |
| Page | no `state` block in `estimates.json`, so `wq.js` falls back to `{code: 'MI', name: 'Michigan', ...}` | a `state` block |

Already shared, Michigan included: the page and `wq.js`; ERA5 cells and their correction (model 1.8), staff water and
lake-source results; state rules as data (`waterledger.rules`, `rules/<st>.toml` for all twelve states, 3.27.0, which
both providers and the page's `rules.json` read); the sewer plant ranking (`wastewater.rank`, Nov 12); the nearest
sizable water system (`supply.nearest_sizable`, 3.9.0); the Great Lake within 5 km (`greatlakes.near`); a place no
utility territory covers taking the nearest served place's utilities; downstream paths past the state line
(`receiving.past_the_line`); and USGS's 2015 county estimate carried beside EGLE's (`county_water_use_usgs`).

## The rule: base plus layers

Every state is built by one builder. For each category of place data, the national source is the base. A state can add
its own layer, and a layer does one of two things:

- **adds** something the base doesn't have (household wells, trout streams), or
- **replaces** the base for that state, where the state's own source is better (reported withdrawals in place of USGS's
  2015 estimates).

County water use already works this way: `wateruse.state_layer(state)` replaces USGS's estimates with Ohio's, Texas's
and Virginia's own records (`wateruse.STATE_LAYERS`), and Michigan's snapshot passes EGLE in through
`write_water_use(state_layer=egle_layer())`. This note uses the same pattern for every category. A layer lives in
`waterledger_data` with the state's other sources, is registered by state and category, and is recorded in the
snapshot's manifest (`layers`: category, source, adds or replaces). The provider reads the layers wherever a snapshot
has them; nothing in the provider asks which state it is.

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

This is the add-state process in two passes (Andrew, Nov 9): a state first goes on with the national base alone; a later
deep dive adds its own layers one at a time, each kept only where it measures better. Michigan is a state whose deep
dive was done first; moving it onto the base keeps the layers that earn their place.

## Michigan, category by category

"Compare" means the numbers are measured side by side before choosing. "Done" is work landed since Nov 9 that this note
needed; "left" is what the build still has to do.

| Category | Michigan today | Base today | Plan | Done since Nov 9 / left |
|---|---|---|---|---|
| Places | 1,541 county subdivisions by Census LSAD (1,122 townships, 118 charter townships, 301 city records; 18 cities cross a county line and have two), no FUNCSTAT filter (`places.municipalities`) | `census.places`: active Census places, active county subdivisions and counties. In Michigan: the same 1,240 townships, but cities as 281 Census places with 7-digit GEOIDs, plus 252 villages and 83 counties | Keep Michigan's list and GEOIDs through a state places rule in the base builder | Left: the places rule |
| Water systems, nearest sizable system | EPA service areas queried place by place (`places.enrich`); nearest sizable by `supply.nearest_sizable`, stored in the site files | `supply.systems_by_place` (bulk overlay); the same nearest rule | Base | Done: the nearest rule is shared. Left: the overlay path, compared in the before and after record |
| Sewer plants | `wastewater.plants("MI")`, ranked by `wastewater.rank`, distances from map coordinates (about 200 m) | the same, at true positions | Base (true distances) | Done: one ranking. Left: true positions, which come with the provider |
| Watersheds, downstream path, impairments | WBD overlap per place (`places.enrich`); ATTAINS by assessment unit ID with Michigan's recodes (2026 cycle); paths past the state line | `receiving.watersheds_by_place` (its sliver and mostly-inside rule); ATTAINS assessment units to HUC12 (table 7) | Base for watersheds and paths; layer (replaces) for impairments (step 2, below) | Done: paths past the line; compared Nov 25. Left: the impairments layer |
| Trout streams | Michigan DNR (`waters.trout_by_huc12`), `Reach.coldwater_streams` | none (`not_covered`) | Layer (adds) | Left |
| Household wells | EGLE Wellogic (`waters.household_wells`), `Supply.household_wells` | none (`not_covered`) | Layer (adds) | Left |
| County water use | EGLE 2025 reported withdrawals, `egle_layer()` rebuilt from the site file's numbers; USGS 2015 beside it | USGS 2015, or a state layer (OH, TX, VA) | Layer (replaces), in `wateruse.STATE_LAYERS`, read from the names-removed EGLE file the package ships (`states/mi/inputs/`) | Done: USGS carried beside EGLE. Left: the move |
| Design storms | NOAA Atlas 14 at each county's internal point (`places.county_design_storms`) | the same (`divisions.design_storms`) | Base | Left: confirmed identical in the record |
| County rainfall | NOAA Climate at a Glance, 1991-2020 (`waters.county_precip`) | the same URL and period (`divisions.rain_in`) | Base | Left: confirmed identical in the record |
| Cooling weather | ERA5 cells | the same | Base | Done (model 1.8) |
| Lake-source cooling | `national.climate.lake_results` | the same | Base | Done |
| Road salt regions | eight regions, `provider.SALT_DAYS` from NOAA ISD-Lite by the national method | NOAA climate divisions (ten in Michigan) and their stations, named "MI climate division N" | Layer (replaces), with the eastern Upper Peninsula taking NOAA division 2 (decision 3, measured below) | Left. NOAA's division names in every state also left |
| Golf course water | median of 453 EGLE-reported courses, 43,500 gal/day, in `estimates.json` | GCSAA's North Central median, 36,200 gal/day (`wateruse.golf_regional`; no Michigan entry in `GOLF`) | Layer (replaces), as Ohio's ODNR figure | Left. `wateruse.golf` marks "state reports" only when `odnr_wwfr` is a source; it needs a basis field |
| Electric utilities | MPSC territories, by area share | HIFLD territories (PNNL's copy), the place's own utility first, then EIA-861 customers (model 1.9) | Layer (replaces); the base gains an EIA-861 county screen in every state (decision 4) | Left: both |
| Balancing authority | a hand list of seven Michigan utilities in PJM (`provider.PJM`); `era5.cell_bas` gives every cell MISO and PJM | HIFLD control area, else the one RTO EIA-861 lists | Base: measured to give the same seven (decision 5) | Left |
| Nearest served place (no territory) | `provider.nearest_served`, center to center on map coordinates | `national.provider.nearest_served`, edge to edge | Base | Left (comes with the provider) |
| State rules | `rules/mi.toml` through `waterledger.rules` | the same file format, every state | Base reads the state's file | Done (3.27.0); the page reads `rules.json` |
| Source citations | `states/mi/build.py`'s `SOURCES`, `SHORT`, `PARAM_SOURCES`, `CONTEXT`, which `state_data.py` imports | | One shared module; no change in content | Left |
| Page-only fields | `validation` (checks against LBNL, Google, and Michigan applicants and Switch's metered use), `size_examples`, `home_customers`, `home_kwh_month` written by Michigan's builder | `validation: []`; residential figures from `power.residential` | Validation as data per state (decision 9); residential figures from the base | Left |

## Measured, Nov 25

Scripts in the session scratchpad, reading only files on the machine (no downloads): Michigan's snapshot 2026-11-17
(model 1.17, 3.25.0), the HIFLD territory layer for Michigan cached Nov 9, EIA-861 2025 (sales, short form, operational
and utility data), the cached NOAA ISD-Lite station years and NOAA's county-to-division table, and EGLE's 2025 file as
the package ships it. The Nov 9 scripts were not kept, so where a count differs below it may be the station set as
much as the data.

### Utilities

Michigan's top utility for each place (the largest MPSC share) against the base's (HIFLD, ranked):

| | Places | Same top utility as MPSC |
|---|---|---|
| MPSC covers | 1,540 of 1,541 (not St. James township, Beaver Island) | |
| HIFLD ranked by customers (the Nov 9 rule) | 1,541 | 819 (Nov 9: 819) |
| HIFLD with the place's own utility first (model 1.9, the base today) | 1,541 | 837 |

The own-utility rule adds 18 places that agree; the misses are the same as on Nov 9: HIFLD draws DTE over much of the state, and
it ranks first in 280 Consumers Energy places, 130 Great Lakes Energy places, 31 Upper Michigan Energy Resources places,
26 Presque Isle Electric & Gas places and dozens more in the north and the Upper Peninsula. In 34 Indiana Michigan Power
places HIFLD's first utility is Midwest Energy Cooperative.

**Balancing authority.** The two paths differ at 20 places (21 under the Nov 9 ranking): 10 Indiana Michigan Power, 9
Midwest Energy Cooperative and 1 City of South Haven place, all in southwest Michigan, where MPSC's utility is in PJM and
HIFLD's first utility is Consumers Energy (MISO). Applied to MPSC's own 57 utilities by EIA number, the base's rule
(HIFLD's control area, else EIA-861's one RTO) puts exactly the seven of the hand list in PJM and the rest in MISO, with
none left without a region. So the hand list and `cell_bas`'s Michigan case can go (decision 5).

**Not re-run: the EIA-861 county list.** On Nov 9 each source's top utility was judged against EIA-861's Service
Territory file, where each utility lists the counties it serves (MPSC 1,540 of 1,540; HIFLD 1,062 of 1,541; HIFLD with
a county screen agreeing with MPSC at 1,072), and the screen was measured in other states (top utility outside EIA's
list in 5% of Ohio's places, 2% of Virginia's and Texas's, under 1% of Wisconsin's; grid region changed in 8 Texas
places). That file is in EIA's yearly zip (`www.eia.gov/electricity/data/eia861/zip/f861{year}.zip`) but
`power.fetch_eia861` keeps only four of its files, and it is not on the machine. Re-running it takes the 2025 zip
(`fetch_eia861` keeping `Service_Territory_*` too) and the twelve states' cached territory layers; it is step 2 below.

### Road salt

Median winter days with precipitation at 1 C or below, 2005-2024 (NOAA ISD-Lite), the measure `runoff.salt_events`
uses, at every cached station in and around Michigan with at least 15 whole winters (precipitation reported on half the
days): 62 stations, 28 in Michigan. The eight regions' stations reproduce `SALT_DAYS` exactly. NOAA's ten divisions use
Houghton (division 1, 119 days), Pellston (2, 93), Traverse City (3, 89), Alpena (4, 88), Muskegon (5, 67), Saginaw (6
and 7, 64), Grand Rapids (8, 72), Jackson (9, 62) and Detroit Metro (10, 59).

Overall:

- The two differ by 5 days or more at 526 of the 1,541 places (Nov 9: 539), by 20 to 26 days at 88 (88). None differ by
  more than 26.
- At the 964 places within 40 km of a station: mean absolute error 5.6 days for the regions, 6.5 for the divisions
  (Nov 9, 810 places: 4.4 and 4.8). The regions are closer at 274 places, the divisions at 137, and they tie at 553.
- At the 16 Michigan stations neither grouping uses: 16.3 days for the regions (bias +10.2), 13.9 for the divisions
  (+7.7) (Nov 9, ten stations: 10.8 and 9.1). The Upper Peninsula sets this: at its five held-out stations 35.6 and 24.2;
  at the Lower Peninsula's eleven, 7.5 for the regions and 9.3 for the divisions.
- Each place's own nearest station, tried by predicting each Michigan station from its nearest neighbor: 11.0 days at 28
  stations (Nov 9: 10.7 at 32). It does not beat either grouping, as on Nov 9.

Area by area, where they differ by 5 days or more ("closer" is the smaller mean absolute error against each place's
nearest station; where that station is one a grouping uses, the check favors that grouping):

| Region in division | Places | Regions | Divisions | Nearest observed (median distance) | Error, regions / divisions | Closer | Nov 9 |
|---|---|---|---|---|---|---|---|
| Southwest in 8 | 121 | 64 | 72 | Southwest Michigan Regional 57 (22 km), Kalamazoo 64 (23 km) | 3.6 / 10.2 | Regions | Regions |
| Central in 9 | 107 | 71 | 62 | Lansing 71 (25 km), Jackson 62 (19 km) | 3.4 / 5.6 | Regions | Regions |
| West in 5 | 68 | 72 | 67 | Muskegon 67 (43 km) | 4.9 / 0.1 | Divisions | Divisions |
| Thumb in 10 | 49 | 64 | 59 | Flint 64 (20 km), Oakland County 71 (44 km) | 1.1 / 6.1 | Regions | Regions |
| West in 6 | 40 | 72 | 64 | Grand Rapids 72 (60 km), Muskegon 67 (82 km) | 3.9 / 10.1 | Regions | not listed |
| Upper Peninsula in 2 (eastern UP) | 38 | 119 | 93 | Chatham 82 (48 km), Munising 74 (51 km) | 39.4 / 13.9 | Divisions | Divisions |
| West in 9 | 36 | 72 | 62 | Grand Rapids 72 (31 km), Kellogg 63 (27 km) | 2.7 / 7.3 | Regions | Regions |
| North in 5 | 32 | 89 | 67 | Muskegon 67 (86 km), Traverse City 89 (84 km) | 11.9 / 10.5 | Unclear: far from both | Unclear |
| North in 6 | 18 | 89 | 64 | Roscommon 96 (68 km) | 6.6 / 31.6 | Regions | Regions |
| Northeast in 2 | 17 | 88 | 93 | Sault Ste. Marie 101 (34 km) | 13.0 / 8.0 | Divisions | Divisions |

The Nov 9 reading holds: the regions are closer for more places, and their one large miss is the eastern Upper
Peninsula, which they give Houghton's 119 days.

**The eastern Upper Peninsula.** NOAA's division 2 is six counties and 68 places (38 in the Upper Peninsula region, 17
in the Northeast, 13 in the North). Three of its stations have whole records: Sault Ste. Marie 101, Chatham 82 and
Munising 74 (Chippewa County International, 117, and Delta County, 98, have 7 and 8 winters). Each candidate value
checked against each place's nearest of those three, with the candidate's own station left out:

| For division 2's 68 places | Error (days) | Bias |
|---|---|---|
| The regions as now | 28.0 | +17.9 |
| Pellston, 93 (division 2's station, in Emmet County, outside the area) | 12.0 | +5.4 |
| Chatham, 82 | 12.5 | -3.1 |
| Munising, 74 | 16.4 | -16.4 |
| Sault Ste. Marie, 101 | 24.5 | +24.5 |

Sault Ste. Marie, one of the two Nov 9 candidates, reads higher than the rest of the area. Pellston and Chatham tie;
Pellston is NOAA's own choice for the division and independent of the check, so the eastern UP takes division 2 as the
base has it (decision 3). Salt days change at those 68 places: 38 from 119 to 93, 17 from 88 to 93, 13 from 89 to 93.

**A finding outside this note: the western Upper Peninsula.** Both groupings give division 1's 105 places Houghton's
119 days. The division's other two whole-record stations read 65 (Copper Harbor, at the tip of the Keweenaw) and 90
(Ford Airport, Iron Mountain-Kingsford, the nearest station for 56 of the 105 places); against them Houghton runs about
36 days high. It is not a choice between the groupings, so it goes to the health queue rather than this round. The
per-place answer for every state remains each place's own ERA5 cell, corrected to stations as cooling weather is, once
the cells' precipitation is pulled.

### Golf

EGLE's 2025 file (names removed, shipped in `states/mi/inputs/`): 453 courses with a usable report, median 43,500
gal/day (quartiles 20,200 and 77,400), unchanged since Nov 9. GCSAA's North Central median is 40.5 acre-feet a year,
36,200 gal/day; EGLE's median is 1.2 times it. Predicting each course from the others' median misses by a median
absolute log error of 0.63 statewide, 0.64 by region and 0.62 by division (a factor of about 1.9; means 0.87 to 0.89);
the survey figure at every course misses by 0.71. Nov 9 reported 0.81 to 0.85 by a statistic that wasn't recorded; the
conclusion is the same: splitting by area doesn't help, and the statewide reported median stays, as a layer like Ohio's.
Only facilities able to withdraw 100,000 gallons a day report, so it may run high, as Ohio's note says of ODNR's.

### Places

From the cached Census layers: Michigan's 1,240 townships and charter townships are active county subdivisions and keep
their GEOIDs on the base. Its 301 city records are county subdivisions that the base's active-only filter leaves out;
the base would list the cities as 281 Census places with 7-digit GEOIDs instead, and add 252 villages and 83 counties.
So the state places rule is needed to keep `wl.place("2608130860")` and every saved scenario working.

### Not measured

- **Watersheds and impairments, base against Michigan's.** The base's ATTAINS and WBD pulls for Michigan aren't cached;
  it takes the receiving stage of `build-state MI` (step 2).
- **Water systems by the base's overlay.** Not cached for Michigan; same stage.
- **County rainfall and design storms.** Same source, URL and period on both paths, so expected identical; the before
  and after record confirms it.
- **The EIA-861 county screen**, in Michigan and the other states (above).

## Step 2, measured Nov 25

Scripts in the session scratchpad (`0011-measure/county_list.py`, `screen_variants.py`, `base_mi.py`, `base_vs_mi.py`).
EIA-861 2025 was fetched again with the Service Territory file kept (`fetch_eia861`, this branch). The base's supply
and receiving stages were run for Michigan's 1,541 places on the 2026-11-17 places, downloading what they needed, and
compared with the before record (`tests/data/michigan_before_0011.json.xz`).

### The EIA-861 county list

EIA's Service Territory file lists the counties each utility serves. Two fixes were needed before the check means
anything:

- Virginia's independent cities are "Alexandria City" in EIA's file and "Alexandria" in the snapshot; the county FIPS
  (510 and up) tells them apart.
- A utility the list doesn't have in the state at all is unknown, not ruled out. FirstEnergy's Pennsylvania companies
  (West Penn, Met-Ed, Penn Power, Penelec) were merged in 2024 under one new EIA number. HIFLD still carries the old
  numbers, which are top at 431 Pennsylvania places.

The base's top utility (today's rule: own utility first, then EIA customers) is listed for the place's county at:

| | MI | OH | VA | TX | WI | IN | MN | PA | GA | IL | NY | AZ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Places | 1,541 | 2,318 | 312 | 1,481 | 1,922 | 1,661 | 2,719 | 2,622 | 697 | 2,807 | 1,584 | 106 |
| Top lists the county | 69.4% | 95.3% | 99.7% | 98.1% | 99.8% | 99.3% | 99.2% | 82.9%* | 97.8% | 97.9% | 99.4% | 95.3% |

\* Pennsylvania's shortfall is the retired FirstEnergy numbers, not a wrong utility.

**The list has errors of its own**, so a screen that drops whatever it leaves out is wrong in places:

- Georgia Power lists 155 counties but not Chatham, where it serves Savannah. A blind screen hands Savannah and
  Pooler to Canoochee EMC.
- A city's own utility lists its whole county. A blind screen gives Norman County's townships to the City of Ada (MN)
  instead of their co-ops.

Three versions were judged in Michigan against MPSC's territories, which are independent of both HIFLD and EIA's list
(top utility agrees with MPSC's, of 1,540 places):

| Screen | Agrees with MPSC |
|---|---|
| None (today's base) | 837 |
| Blind | 1,090 |
| No municipal promoted outside its own place | 1,090 |
| That, and the replacement must cover at least as much of the place as the utility dropped (**chosen**) | 1,073 |

The chosen screen gives up 17 Michigan places (where MPSC replaces the base anyway) and fixes Savannah and the City of
Ada. It changes the top utility at 51 places in Ohio, 28 in Texas, 17 in Pennsylvania, 13 in Minnesota, 41 in
Illinois, 10 in Indiana, 5 in Georgia, 5 in Arizona, 3 in Wisconsin, 1 in New York and none in Virginia. The
balancing authority changes at 43 places:

- Texas, 8 (MISO or SPP to ERCOT: Dallas, Coppell, Richardson, Grand Prairie and others);
- Illinois, 23 (PJM to MISO: Henry County's places from ComEd to Ameren);
- Georgia, 5 (Southern to TVA: Blairsville, Hiawassee, Fannin, Towns, Union);
- Arizona, 5;
- Indiana, 2.

Each place is listed in `screen_variants.json` for the methods log. Decision 4 stands, with the screen as chosen
here.

**For the health queue, not this note:**

- Texas: the base names a co-op (Denton County Electric, then Farmers Electric after the screen) as Dallas's top
  utility, where Oncor delivers. Delivery-only utilities report no customers, so they rank low in ERCOT's open
  areas. The screen fixes Dallas's balancing authority but not its utility.
- Pennsylvania: the retired FirstEnergy numbers have no EIA-861 customers, so co-ops and small boroughs outrank
  Penelec, West Penn and Met-Ed (Scalp Level and Westmont show Somerset Rural Electric today). The numbers need a map
  to FirstEnergy Pennsylvania's new one.

### Water systems

At the 5% line where a system is taken to serve a place, the base and Michigan give the same systems at 1,522 of
1,541 places. All 19 differences sit within a point of 5% (map coordinates against true outlines), and 6 of them
flip whether the place has a system. The base also lists systems on 0.5–5% of a place (535 places), as it does in
every state. Base, as decided.

### Watersheds and paths

The main watershed is the same at 1,523 places. The 18 that differ split near-equal shares. The base lists every
watershed on 1% or more of a place; Michigan's list stops sooner. Only 9 of the base's 1,785 extra entries cover 10%
or more of a place. Base.

### Impairments

Along the downstream paths, the base's impairments match Michigan's on 8,041 of 10,914 reaches (74%), and TMDLs on
88%. The base nearly always lists more. Both read the 2026 cycle; the difference is how a unit is placed:

- The base reads EPA's table of assessment units by HUC12 (ATTAINS layer 7). It links a unit to every HUC12 its
  catchments touch. Belle Isle-Detroit River (040900040503) picks up the streams of three neighbouring HUC12s (units
  named "Rivers/Streams in HUC 040900040407" and others).
- Lake Erie's, Lake Huron's and Lake Superior's units land on every shore HUC12.
- Michigan's path places each unit in its own watershed.

Michigan's placement is the better one, so **impairments become a Michigan layer that replaces the base's**. It is
the state's own reading of EGLE's units, kept because it doesn't measure worse. The base's placement leaks in every
state, which goes to the health queue: place a unit by where most of it lies, not where it touches.

### Build time

The base's `watersheds_by_place` took 7.4 hours for Michigan's places. Every other stage took under 15 seconds.
`build-state MI` runs it, so step 4 has to make it fast, or cache it, before Michigan's snapshot is built on the base.

## Step 6, the after record (Nov 25, 2026)

Every Michigan answer again from a snapshot built on the base with Michigan's layers (`waterledger snapshot MI`, 2.5 minutes), against
the before record. That covers 11,112 cases at 1,541 places. 276 fields differ, at some place, for some case (281 before the 5% fix below); the full list, with counts,
largest changes and examples, is `0011-differences.md`. Each has one of the causes below. No better Michigan source was dropped.

**The water estimates.** Cooling, staff and lake-source water are the same, with three exceptions:

- At the 325 places on a Great Lake, lake-source figures differ in the sixth figure. Michigan's path read the site files, which round
  them; the base keeps full values.
- Delhi, Caldwell and Rose townships move to the neighbouring weather cell, by their true Census point.
- Twelve places change a default (next item).

Getting here took one fix in the base for every state: the staff-water draws, 400 as the model has them, not 200.

| Cause | Places | What changes | Verdict |
|---|---|---|---|
| Labels | 1,541 | `provider` reads "national" (decision 8); source ids are the base's (`noaa_isd`, `wellogic`, `usgs_wu2015` and others listed); the data date is the snapshot's; the golf and power notes are worded as for every state; reference gains `not_covered` | Expected |
| True positions | 1,540 | Census internal points in place of the page's map coordinates (lat and lon within about 0.001 degree), so distances to sewer plants and water systems change by up to a few hundred metres; at 72 places two plants swap order | Expected |
| Default source or wastewater | 12 | A distance crossing the 10 km line or a share crossing 5%: Irving, Butterfield and Lake townships lose the sewer default; East Bay, Cambria, Rives, Kalkaska, Burlington and Edwards gain it; Mackinaw and Crockery lose the public water default, and East Bay, Kalkaska and Vernon gain it | Expected; listed by place in the differences file |
| Eastern Upper Peninsula | 68 | Region, name and station, and road salt at 93 days (decision 3) | Expected |
| Water systems at the 5% line | 19 | A system that serves the place is one on 5% of it or more, as Michigan's files always listed them. After a first run, where the base listed systems down to 0.5% and about 170 places gained a comparison with one barely in them (Greenbush Township with Harrisville's system), the base was changed for every state to list only the systems that serve a place (3.28.0). What remains is 19 places whose shares sit within a point of 5% by true outlines, and comparisons or the water-system level change at 30 and 6 of them | Expected; fixed in the base for every state |
| County water use keys | 1,541 | `county_use_mgd` uses the shared categories (`public_supply`, `golf`, and a `total`), as in every state, in place of EGLE's group names. The numbers are EGLE's | Expected; the page's labels are step 7's job |
| Watersheds | 1,473 | The base also lists watersheds on 1–5% of a place; the main one differs at 28 places and the HUC8 at 60, where shares are near equal | Expected |
| Utilities | 1,541 | MPSC's territories as before, the same top utility everywhere but one place (Homeworks Tri-County to Consumers, by true outlines); shares from true outlines at 190 places; loads unrounded | Expected |
| Power options | 1,541 | MISO's withdrawal is the Siddik table's 54.8 L/kWh (the base reads the shipped table in every state), not the 57.1 typed into Michigan's builder, which matches no column of the table; a PJM grid average is offered, since seven Michigan utilities are in PJM | **For Andrew** (MISO): expected unless 57.1 came from somewhere the table doesn't |
| Rain | 17 | County rainfall in the fourth figure: the same NOAA series, read again | Expected |

**For the health queue, not this note:** two problems step 2 found in other states:
Texas's delivery-only utilities ranked last in ERCOT's open areas, and FirstEnergy Pennsylvania's retired EIA numbers.

## No better estimate lost: the check

Step 1 writes every number `wl.place(...)`, `place.context()`, `site.estimate()` and the provider's `reference()` give
for all 1,541 places, at the starting settings and every cooling design (lake-source where a place is on a Great Lake),
from 3.27.0 and Michigan's current snapshot, plus the site files. After the switch, the same numbers again. Every
difference gets a cause:

- **expected**: the base or a layer is better (true distances in place of map coordinates, a newer source, a measured
  choice in this note);
- **bug**: a better Michigan source was dropped or read wrong. These are fixed before release.

Andrew reviews the list of differences and their causes before anything is released or deployed. A default rule that
flips at the 10 km line, because a distance moved by 200 m, is listed by place. The methods log records the data
changes, and the model version is unchanged (no model changes). Northline's record of its reports is separate (its
plan's step 4) and catches what reaches the reports.

## Places

Michigan's GEOIDs are public API: `wl.place("2608130860")` and every saved scenario use them. They stay. The base
builder gains a state places rule (which Census layers and codes make a state's places); Michigan's keeps cities,
townships and charter townships as county subdivisions by LSAD, as now, with no counties. Adding villages, or counties,
is a separate question for later.

## The 3.x promise

- `waterledger.scenario`'s Michigan readers (`data`, `place`, `find`, `scenario`, `src_for`, `dest_for`, ...) and
  `waterledger.states.mi` keep working through 3.x with a `DeprecationWarning` and a CHANGELOG **Deprecated** entry.
  The shared functions in `scenario.py` (`cooling_estimate`, `lake_estimate`, `check_lake`, `land_default`,
  `for_plant`, `electricity`, `grid_water`) stay where they are.
- `wl.place`, `Place`, `Context` and `Estimate` keep their shape for Michigan. Fields Michigan alone fills
  (`Supply.household_wells`, `Reach.coldwater_streams`, the EGLE groups in `county_use_mgd`, Michigan's region in
  `Climate.region`) are filled from the layers. The parts' `provider` field changes from "MI" to "national", with the
  layers' sources in each part's `sources` (decision 8).
- Packages up to 3.27 read Michigan through the site files: the local site, else the snapshot's `michigan/` folder,
  else the published file at waterledger.org/mi/data/, which `scenario.data` downloads when the folder is missing. So
  new snapshots can drop the folder as long as the site files keep their shape. A test reads the new site files with
  3.27's `scenario.py` and Michigan provider, for every place.
- Snapshots already published are not changed.

## The site

`state_data.py` writes Michigan's files like every other state's, and `mi_data.py` is retired; `engine/states.toml`
marks Michigan `national`. Michigan's `estimates.json` gains a `state` block listing its layers, so the fallback in
`wq.js` can go. The rule text is already data (`rules.json`). The page change is small, but it changes live numbers, so
Andrew checks it locally before any deploy.

## Not in this note

- The water user contract (0010), apart from its decision 5, which follows on this path (step 8).
- Villages and counties as Michigan places; Michigan's learn, changelog and tracker pages (unchanged).
- The western Upper Peninsula's salt days (health queue) and salt from ERA5 cells (later, every state).

## Order of work, from where things stand (each step its own commit)

1. **The before record**: every Michigan number from today's path (3.27.0, snapshot 2026-11-17), for all places and
   designs, the context fields and `reference()`, kept compressed in `tests/data/` as the contract's record is.
2. **The measurements this refresh could not run.** *Done Nov 25* (above): the county screen, guarded, goes into the
   base. Impairments become a Michigan layer. Water systems, watersheds and paths take the base.
   `watersheds_by_place` has to be made fast for Michigan before step 4.
3. **Layers in `waterledger_data`**: Michigan's wells, trout streams, impairments, MPSC utilities, salt regions (with division 2 for
   the eastern UP) and golf median, registered by state and category; EGLE moved into `wateruse.STATE_LAYERS`, read
   from the shipped file; `wateruse.golf` given a basis field. The citation list and `CONTEXT` moved to a shared module.
   The state places rule. In the base, for every state: the EIA-861 county screen and NOAA's division names (these
   change other states' context; recorded in the methods log).
4. **The base builder reads layers** and writes them into the snapshot, with the manifest's `layers`; `build-state MI`
   runs it; the CLI's and the workflow's Michigan branches go.
5. **The national provider reads layers; Michigan uses it.** `states.Provider`'s own-provider branch, `cell_bas`'s
   Michigan case and the PJM list go; the old readers warn. Validation rows as data (decision 9).
6. **The after record** and the list of differences with causes, for Andrew.
7. **Northline**: `state_data.py` writes Michigan; `mi_data.py` retired; `states.toml` `national`; the `wq.js` fallback
   removed; `check_parity`; Andrew's local check of the page.
8. **0010's decision 5**: providers reduced to the place side, now that there is one provider path. Its own commit,
   after the after record, so the record isolates this note's changes; its own identity test (`test_contract_identity`).
9. READMEs, `docs/add-a-state.md`, CHANGELOG (Deprecated), the methods log (short and long notes); a minor release and a
   Michigan snapshot, each on Andrew's word. Then Northline rebuilds its reports' record (its plan's step 4).

## Decisions (agreed, Andrew, Nov 25, 2026)

1. **Base plus layers, one builder.** Each layer adds or replaces, and replaces only with a stated reason.
2. **No better estimate lost:** the before and after record, every difference with a cause, Andrew's review before
   release.
3. **Michigan's regions stay as a layer, with the eastern Upper Peninsula taking NOAA's division 2** (its six counties,
   68 places, at Pellston's 93 days). Changed from Nov 9, which proposed Sault Ste. Marie or Pellston: left out of its
   own check, Sault Ste. Marie misses by 24.5 days and Pellston by 12.0 (the regions as now: 28.0). The regions are
   closer at more places elsewhere, and the names are Michigan's. The change is a correction recorded in the methods
   log.
4. **MPSC replaces HIFLD in Michigan** (re-measured: HIFLD's top utility agrees with MPSC's at 837 of 1,540 places
   under today's rule), and the base gains the EIA-861 county screen in every state, once step 2 re-runs its measurement.
   **EGLE's golf median replaces the survey** (43,500 against 36,200 gal/day).
5. **The balancing authority comes from the base** (new): its rule gives the same seven PJM utilities as Michigan's hand
   list, so the list and `cell_bas`'s Michigan case go. The 20 places where the region differs today differ because of
   which utility comes first, which decision 4 settles.
6. **Michigan's places and GEOIDs stay**, by a state places rule; villages and counties later.
7. **New snapshots drop the `michigan/` folder**; packages up to 3.27 fall back to the published site files, which keep
   their shape, with a test.
8. **Context's `provider` reads "national" for Michigan too** (new), with each layer's source listed in the part's
   `sources`, as Ohio's water use already is. Anything testing `provider == "MI"` changes (one test in this repo); the
   CHANGELOG says so.
9. **Validation as data per state** (new): Michigan's validation rows (its applicants' figures and Switch's metered use)
   move from its builder into a data file the shared code reads, so any state can carry reported figures, as the
   add-state bar has them come in as methods updates.
