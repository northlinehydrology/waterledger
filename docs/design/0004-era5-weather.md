# 0004: ERA5 weather at every place's nearest cell

Status: **proposed, Nov 3, 2026; not built.** The direction was decided by Andrew on Nov 1, 2026, and the rule for
mostly-water cells on Nov 3; this note is the plan for review before the build. It changes [0002](0002-national-tier.md)
decision 4 (climate) and Michigan's eight regions ([0001](0001-schema-and-api.md) decision 5), and the snapshot format of
[0003](0003-data-releases.md).

## Decisions already made (Nov 1 and Nov 3, 2026)

1. **Every place in every published state takes its cooling weather from its nearest ERA5 grid cell.** This replaces
   Michigan's eight climate regions and the other states' one station per NOAA climate division. Cells are not grouped:
   each cell is run on its own, and its results go in a small file the page loads for its place.
2. **Distribution correction is a later, separate step.** Quantile mapping that anchors ERA5 to nearby stations comes
   after this change, as its own model version, with Andrew leading the method. This plan keeps what it will need
   (below) but builds none of it. *Nov 3: Andrew asked for it now; the method, a prototype and whether it ships in model
   1.8 are in [0005](0005-era5-quantile-mapping.md).*
3. **A place whose nearest cell is mostly water takes the nearest cell that is at least half land** (decided Nov 3,
   2026: "use b nearest land cell"). Mostly water means an ERA5 land-sea mask under 0.5; the nearest land cell is the
   nearest by great-circle distance from the place's internal point with a mask of at least 0.5. 189 places move. Every
   place records the cell it uses, that cell's distance and land fraction, and whether the rule moved it (section 2).

It is a model change: model 1.8 after model 1.7 (3.9.0, Nov 2, 2026).

## 1. Data source

Checked Nov 3, 2026. Every ERA5 copy is under the licence ERA5 has carried since July 2, 2025, **CC-BY 4.0**, so
commercial use is allowed with attribution:

> Generated using Copernicus Climate Change Service information [year]. Neither the European Commission nor ECMWF is
> responsible for any use that may be made of the Copernicus information or data it contains.

The dataset is cited as Hersbach et al. (2023), ERA5 hourly data on single levels from 1940 to present, C3S Climate Data
Store, doi:10.24381/cds.adbb2d47, with Hersbach et al. (2020), QJRMS 146(730): 1999-2049.

| Source | Access and cost | Variables | One cell, 1995-2024 | Use here |
|---|---|---|---|---|
| **Copernicus CDS, `reanalysis-era5-single-levels-timeseries`** | Free ECMWF account and API key (`cdsapi`); no fee. Labeled experimental by ECMWF | 2 m temperature, 2 m dew point, surface pressure | **One request** (cost 108 of a 760 limit, from CDS's costing API), CSV or NetCDF | **The build's source.** Official, one request per cell, about 1,300 requests in all |
| Open-Meteo's open-data copy on AWS (`s3://openmeteo/data/copernicus_era5`) | Anonymous, no key, no fee (AWS Open Data, CC-BY 4.0). Not bound by Open-Meteo's API terms | 2 m temperature and dew point; no surface pressure (`pressure_msl` only) | About 60 ranged reads of yearly files; **1.5 s per cell-year per variable** (measured here); values stored to 0.05 C | **The no-credentials path**: tests, reproduction, a user rebuilding a state, and this note's checks |
| NSF NCAR ERA5 on AWS (`s3://nsf-ncar-era5`) | Anonymous, no fee (AWS Open Data); UCAR terms CC-BY 4.0, doi:10.5065/BH6N-5N20 | All three | Monthly NetCDF files (about 1.1 GB) chunked 27 h x 139 x 277 cells; about 135 GB read for all cells at once | Archival fallback if both above go away |
| Google ARCO-ERA5 (`gs://gcp-public-data-arco-era5`) | Anonymous, Google-hosted | All three | One global field per hourly chunk: about 1.9 TB read for any number of cells | No (used once here for the land-sea mask, one 2 MB field) |
| Open-Meteo API | Free tier is non-commercial only; historical data needs the paid Professional plan | | | **No.** Michigan's current weather came through it (best match, not ERA5 alone) |

Not used: AWS `era5-pds` (deprecated, listing denied), Microsoft Planetary Computer (ends 2020).

**Only temperature and dew point are needed.** The cooling model takes air temperature and relative humidity, and
relative humidity comes from temperature and dew point alone, by the same Magnus form the station records use
(`waterledger_data.climate.isd_hourly`, Alduchov and Eskridge 1996). Surface pressure is fetched from CDS anyway (it
costs nothing in that request) and kept in the raw cache, for the BMI components' specific-humidity path and for
quantile mapping, but no estimate depends on it.

**ERA5, not ERA5-Land.** ERA5-Land (0.1 degree) has the same variables in a CDS time-series dataset, but it is a land
surface rerun forced by ERA5, has no values over the sea, and would need 3,751 cells here. ERA5 at 0.25 degree is the
decision.

**The raw cache.** Each cell's hourly series is kept as fetched (UTC, unrounded NetCDF from CDS) in the private R2 raw
cache planned alongside this change, keyed by cell and fetch date, with its CDS request and checksum. A rebuild, a new
model version or quantile mapping then reads the cache, not CDS. About 2.5 MB per cell compressed (three variables,
263,000 hours, float32) [estimate], about 3.3 GB for the four states.

## 2. Cells

A place's nearest cell is the ERA5 grid point nearest its Census internal point (the `lat`, `lon` every place already
has): latitude and longitude each rounded to the nearest 0.25 degree. Counted from the 2026-11-02.2 snapshots:

| State | Places | Nearest cells | Most places in one cell | Distance to the cell center: median, max |
|---|---|---|---|---|
| Michigan | 1,541 | 313 | 20 | 9.3 km, 16.8 km |
| Ohio | 2,318 | 211 | 35 | 9.7 km, 17.3 km |
| Virginia | 322 | 157 | 6 | 9.9 km, 17.7 km |
| Texas | 1,481 | 619 | 16 | 10.3 km, 18.0 km |
| **All four** | **5,662** | **1,294** (6 shared across state lines) | | |

The estimate was about 1,700; the count is 1,294. (ERA5-Land would need 3,751.) County rows are counted at their own
internal point; without them Virginia needs 131 cells and Texas 551.

**Cells that are mostly water: decided Nov 3, 2026, the nearest land cell.** 189 places have a nearest cell whose ERA5
land-sea mask is under 0.5, so its 2 m air is mostly over lake or sea: Michigan 116 (45 cells, Great Lakes shores, bays
and islands), Ohio 35 (8 cells; Lake Erie from Toledo to Conneaut, and the Bass Islands), Virginia 23 (9 cells; the
Eastern Shore and Hampton Roads) and Texas 15 (4 cells; Corpus Christi Bay and Galveston). Their air runs cooler in
summer and milder in winter than inland air, which lowers hybrid and assist water. Andrew chose option (b), the nearest
land cell, over (a), the nearest cell for every place: **such a place takes the nearest cell, by great-circle distance
from its internal point, whose mask is at least 0.5.** (The ring search and its tie-break are in
[era5-check/land_rule.py](../methods/era5-check/land_rule.py).) With the rule:

| State | Places moved | Cells | Most places in one cell | Moved: median, max distance | Distance, every place: median, max |
|---|---|---|---|---|---|
| Michigan | 116 | 272 | 20 | 16.9 km, 60.3 km | 9.7 km, 60.3 km |
| Ohio | 35 | 203 | 38 | 17.4 km, 28.0 km | 9.7 km, 28.0 km |
| Virginia | 23 | 148 | 13 | 34.4 km, 56.6 km | 10.4 km, 56.6 km |
| Texas | 15 | 616 | 16 | 20.3 km, 31.4 km | 10.4 km, 31.4 km |
| **All four** | **189** | **1,233** (6 shared) | | 17.8 km, 60.3 km | |

Every place's assignment, with its nearest cell for comparison, is in
[era5-check/cell_assignment.csv](../methods/era5-check/cell_assignment.csv). Of the 189, 165 move 30 km or less (all of
Ohio's and all but one of Texas's, which go 15-31 km inland from the bays). The farthest moves, including all 15 over 40
km, are in Virginia and Michigan:

- **Virginia's Eastern Shore.** Its places sit on mostly-sea cells, and the nearest land cell is not always across the
  bay. Cape Charles, Cheriton, Eastville and Northampton County (43-52 km) and Nassawadox (57 km) go **across the
  Chesapeake** to cells on the western shore (37.25, -76.50 by Yorktown, land 0.51; 37.50, -76.50, land 0.68). Exmore
  (53 km), Belle Haven (50 km), Painter, Wachapreague and Keller (42-46 km) go **north up the peninsula** to 38.00,
  -75.75 at the Maryland line (land 0.67), as do Melfa, Onley, Onancock, Accomac, Parksley, Accomack County and Tangier
  (25-39 km), and Bloxom and Chincoteague go to 38.00, -75.50 (14-22 km). The earlier draft's "50-63 km across the bay"
  was wrong on both counts: it measured in grid steps, not kilometers, and most Eastern Shore places don't cross the
  bay.
- **Michigan's islands.** Townships whose internal points fall on an island: Isle Royale (Houghton and Eagle Harbor
  townships of Keweenaw County) goes to cells on the Ontario shore, 55-60 km; Beaver Island (Peaine and St. James
  townships) 37-44 km to the mainland; North Manitou (Leland township) 43 km, the Garden Peninsula's tip (Fairbanks
  township) 44 km and Drummond Island 39 km.

**What the rule doesn't change.** It moves only cells under half land. 777 places stay on cells 50-90% land (Michigan 462,
Ohio 172, Virginia 56, Texas 87), and the station check's part-water places show those run low too: Cleveland (0.65),
Port Huron (0.75), Toledo (0.78) and Virginia Beach (0.51) keep their cells. See section 4.

## 3. Run time and how to split the runs

Measured Nov 3, 2026 on Andrew's Mac (Apple M3 Max, 14 cores, 96 GB), model 1.7 (`cooling.run_location`, 400 Latin
hypercube draws plus the central run, every design, 1995-2024 hourly, 262,992 hours):

| Cells at once | Wall time | Each cell | Throughput |
|---|---|---|---|
| 1 | 362 s | 362 s | 362 s per cell |
| 6 | 460 s | 457-459 s | 77 s per cell |
| 12 | 935 s | 924-934 s | 78 s per cell |

Twelve at once is no faster than six: past six processes the runs share memory bandwidth, not cores (each process holds
about 1.2 GB). **Six workers** is the setting. A profile on five years and 20 draws puts 72% of the time in the hourly
heat balance, solved three times for every draw (at average load, at the peak day's load and at full capacity). No
change that keeps the numbers identical removes a large share of it.

Model 1.6 took about 116 s per cell; model 1.7 takes 362 s alone, about three times as long. From the code (not
profiled): twice the draws (400 against 200), and model 1.7's peak day at peak load, a further pass over every hour for
every draw.

**The four states at six workers, about 26 hours of machine time** (1,233 cells with the land rule x 77 s; 28 hours for
the 1,294 nearest cells before it):

| State | Cells | Hours at six workers |
|---|---|---|
| Michigan | 272 | 5.8 |
| Ohio | 203 | 4.3 |
| Virginia | 148 | 3.2 |
| Texas | 616 | 13.2 |

Fetching is separate and smaller. From Open-Meteo's open copy, the 21 cells of the station check took 183 s with 16
threads (about 8 MB of JSON per cell). Reading cell by cell, all 1,233 would take about 3 hours [estimate, linear].
Reading each state's box from each file at once should be much faster, because the files are chunked one row by six
columns, but that was not measured. From CDS it is one request per cell; the queue time was not checked.

**How to split them.** Nothing is scheduled; Andrew starts each part by hand.

- Seven parts of 2.9 to 4.4 hours, each started by hand on an evening or overnight: Michigan in two (136 cells each),
  Ohio, Virginia, and Texas in three (205-206 cells each): `waterledger era5 run TX --part 1/3 --workers 6`.
- A cell's results are written the moment it finishes (`CACHE/era5/runs/model1.8/<cell>.json`), so a stopped part
  resumes where it stopped, as the state builds do now (0003, decision 4). Fetching and running are separate steps, so a
  CDS outage never stops a run that has its weather.
- Cells shared across a state line are run once and copied into both states' snapshots.
- A cell's run depends only on its weather, the model version and the seed, so parts can run on different machines and
  be merged; the merge checks that a cell run twice gives the same numbers.

## 4. Station check

[era5-station-check.md](../methods/era5-station-check.md) reruns the Oct 29 station check on model 1.7 at its 21 places,
adding ERA5 at each place's own cell (scripts and results in `docs/methods/era5-check/`). The runs reproduce the published
snapshot exactly (Findlay, every statistic). In short:

- **Towers:** ERA5 is within 1% of the nearest qualifying station on the average day and 3% on the peak day, everywhere.
- **Inland (cells at least 90% land, 16 places):** ERA5's hybrid average is within 9% of the nearest station at 14 and its
  assist average at 13. In Texas every comparison is within 9%. ERA5 removes the far-station errors: Austin's assist peak day
  was published 20% below San Antonio's station and is 3% below on ERA5; Amarillo's hybrid average was 22% above its own
  airport and is 5% above.
- **The exceptions inland:** Roanoke, a valley airport against a cell that averages in the ridges (14-22% lower), and Ironwood
  (higher than Houghton's station, 150 km away by Lake Superior).
- **Cells that are part lake or sea** (Lorain, Virginia Beach, Cleveland, Port Huron, Toledo): hybrid averages 6-39% and
  assist 11-52% below the shore airports, with design dry-bulbs 2-3 C lower. Lorain's and Virginia Beach's hybrid peak days
  go up (26%, 8%), because a lower design dry-bulb makes a hybrid fully wet sooner.
- **The land rule on those five** (rerun Nov 3): only Lorain (0.40) moves, 16 km to a cell 0.59 land, and its gap narrows a
  little (hybrid average -10% to -8%, assist -39% to -35%, hybrid peak +26% to +18%). Virginia Beach (0.51), Cleveland
  (0.65), Port Huron (0.75) and Toledo (0.78) keep their cells. As a sensitivity, not a proposal, the nearest cell at least
  90% land (17-52 km away) brings Lorain's and Virginia Beach's hybrid averages within 2% of the station; Port Huron's,
  against a station 80 km away, stays about 30% low. So the rule removes the mostly-water cells, but the 777 places on cells
  50-90% land keep the shore bias, which is the reason to treat quantile mapping as the next step, not an optional one.
- **Against what is published today,** across the 21 places: the hybrid average moves -21% to +60% (median -5%), assist
  -50% to +83% (median -8%), and towers by 2% or less.

## 5. The code change

### Package API

`waterledger-data` (fetching):

- `waterledger_data.era5.cell(lat, lon, land=0.5)`: the cell a place uses under decision 3, as a small record: `id`
  (`"43.00_-85.50"`), center, `km`, `land` (its land-sea mask), `moved` (true when the nearest cell is under `land`) and
  `nearest` (the nearest cell's id, km and land, kept so the move can be shown). `land=None` returns the nearest cell
  unconditionally. The land-sea mask ships with the package (2 MB, or the four states' rows only), and the function is
  the one `land_rule.py` here prototypes, tested against `cell_assignment.csv`.
- `era5.fetch(cell, source="cds" | "s3")`: the cell's hourly 2 m temperature and dew point (and pressure from CDS),
  1995-2024, cached raw. `"s3"` is Open-Meteo's open copy, for anyone without a CDS key.
- `era5.hourly(cell)`: `(times, temp_c, rh_pct)` in local standard time from longitude, the form `isd_hourly` and
  `run_location` use, with RH by the stations' Magnus form.

`waterledger` (building and reading):

- `waterledger.national.climate.cell_runs(state, part=None)` replaces `division_runs` for cooling, in every state,
  Michigan included. Michigan's regions and the national tier's divisions stay for what they do now besides cooling:
  NOAA county rainfall and design storms (by county, unchanged), road salt's cold wet days and golf course water (by
  division or region, from station records, unchanged).
- `Climate` (the context) gains `cell`, `cell_km`, `cell_land` and `cell_moved`; `region` and `station` stay,
  describing the rainfall and salt records.
- `site.estimate(weather="cell")` is the default and reads the place's cell file. `weather="region"` is kept as an
  alias of `"cell"` for one release, with a deprecation note. `weather="local"` stays (the model run at the place's own
  point, now on ERA5 from `era5.fetch`, not the Open-Meteo API).
- `Site.to_bmi_config()` fills `design_db` from the place's cell file when a hybrid has no forcing file, and
  `weather.design_dry_bulb` (this release's BMI fix) is the function that computed it, so a BMI user's value, the cell file
  and the page agree.
- CLI: `waterledger era5 fetch ST [--source s3]`, `waterledger era5 run ST [--part k/n]`, then `build-state` and
  `snapshot` as now.

### Snapshot format 3

- `places.json`: each place gains `cell` (the id of the cell it uses), `cell_km` (great-circle distance from its
  internal point to that cell's center), `cell_land` (that cell's land-sea mask) and `cell_moved` (true for the 189 places
  the land rule moved). A moved place also carries `nearest_cell`, `nearest_km` and `nearest_land`, so its methods note
  can say what was skipped and why. These are the columns of `cell_assignment.csv`.
- `cells/<cell>.json`, one per cell: `per_100mw` (the same structure the divisions and regions carry now), plus
  `lat`, `lon`, `land`, `design_dry_bulb_c`, `period`, `hours`, `source` and the attribution. About 15 KB unrounded and
  4.5 KB gzipped; at four significant figures 9.5 KB and 1.9 KB gzipped. Rounding is the site's choice, not the
  snapshot's (snapshots keep full precision, as now).
- `cells/index.json`: every cell's id, center, land fraction, places (and which of them the land rule moved there) and
  the checksum of its file. `manifest.json` records the rule (`"cell_rule": {"land_at_least": 0.5}`).
- `climate.json` no longer carries cooling results for divisions or regions; it keeps their station records for rainfall
  and salt.
- `manifest.json`: `weather` names the dataset, DOI, period, fetch dates and the attribution; `format: 3`.
- Sizes: Michigan +4.1 MB, Ohio +3.0 MB, Virginia +2.2 MB, Texas +9.2 MB unrounded [estimate from the file size above];
  the page downloads one cell file per place viewed.
- A package that reads format 2 keeps working on the snapshots it reads now: `by_model` means model 1.7 packages never
  see a model 1.8 snapshot.

### The site

The calculator loads `cells/<cell>.json` for the chosen place instead of reading its region's or division's numbers
from the state file. The methods pages say "ERA5 at the nearest 0.25-degree grid cell that is at least half land,
about 10 km from the place", and each place's note gives its cell, distance and land fraction, and for a moved place,
that its nearest cell was mostly water and how far it moved. This is a change in the site's repository, made after the
package release and Andrew's approval.

### What quantile mapping will need (not built now)

Proposed and prototyped in [0005](0005-era5-quantile-mapping.md); the hooks below are what it uses.

- The raw cell series (R2 cache), unrounded, in UTC.
- Station-cell pairs: every ISD station passing the snapshot rule (85% of hours, 1995-2024), with its nearest cell; the
  station check below is the first set.
- A hook in `era5.hourly(cell, correct=None)` where a correction can be applied before the cooling run, so the corrected
  and uncorrected runs share everything else.
- A cell file has room for `correction` (method, stations, version), empty until then.

## Short note for the methods pages (draft, for when it ships)

> **Weather.** Each place's cooling water comes from the hourly weather of its nearest ERA5 grid cell, 1995-2024. ERA5
> is ECMWF's global reanalysis for the Copernicus Climate Change Service, on a 0.25-degree grid; the cell's center is
> about 10 km from the place on average and, for all but 189 places, never more than 18 km. Where the nearest cell is
> mostly lake or sea (those 189 places, on the Great Lakes, Lake Erie's islands, Corpus Christi and Galveston bays and
> Virginia's Eastern Shore and Hampton Roads), the place takes the nearest cell that is at least half land instead,
> usually 15-30 km away. On Virginia's Eastern Shore that cell is 14-57 km away, across the Chesapeake for Cape Charles,
> Cheriton, Eastville, Nassawadox and Northampton County and up the peninsula at the Maryland line for most of Accomack
> County; Isle Royale's is on the Ontario shore. A reanalysis smooths local extremes, so a site's own hottest hours can
> be hotter than its cell's, which matters most for hybrid and evaporative assist designs. Before model 1.8, Michigan
> used eight regional points and other states one airport station per NOAA climate division.
