# 0005: Quantile mapping ERA5 to stations

Status: **decided Nov 4, 2026, for model 1.8; prototyped, not built.** Andrew asked for it on Nov 3 ("Let's do the quantile
mapping") after the land rule of [0004](0004-era5-weather.md) (decision 3) turned out to move only the mostly-water cells.
He leads the method. The proposal of Nov 4 gave the choices, a recommendation for each and a prototype on the station
check's 21 places. The same day he accepted it with three decisions ("Yes to all three", below), and the prototype was rerun
under them. The method ships as `waterledger_models.quantile_mapping`. Scripts and results are in
[docs/methods/qm-check/](../methods/qm-check/). No snapshot changes until the model 1.8 build, which waits for Andrew.

## Decisions (Andrew, Nov 4, 2026)

1. **The 90% land cutoff stays.** Cells under 90% land are corrected, and cells at least 90% land keep ERA5 as it is.
2. **Shore stations only.** A shore cell is corrected only from stations that are themselves near water. The test chosen
   is the cells' own: a station is a shore station when its own ERA5 cell is under 90% land. That is the cell the land
   rule would give a place at the station. A shore cell with no shore station within 100 km stays uncorrected and is
   flagged, as cells with no station were before.
3. **More stations.** (a) ISD records are linked across a change of station ID, so a site whose record is split between
   IDs can still pass the 85% rule. (b) Environment and Climate Change Canada's hourly stations are added under the same
   completeness rule and quality checks.

Ship it with ERA5 as model 1.8. The rest of the method is as proposed (sections 1-6).

## The problem

On the station check, ERA5's cells that are part lake or sea run cool next to the shore airports. After the land rule, 777
places still sit on cells 50-90% land (Michigan 462, Ohio 172, Virginia 56, Texas 87). At the check's five shoreline places
the uncorrected cell is 15% low on the hybrid average day and 34% low on assist (means against the nearest station),
with design dry-bulbs 2-3 C low. Inland, ERA5 is already within the scatter between stations.

## The method

### 1. What is corrected

| Option | For | Against |
|---|---|---|
| **T and the dew-point depression D = T - Td** (chosen) | D at or above 0 after correction gives Td at or below T and RH at or below 100% by construction; T and D keep ERA5's own hour-to-hour timing | Corrects two margins, not their joint distribution |
| T and Td separately, then Td clipped to T | Simplest | Clipping makes saturated hours that neither record has |
| T and RH | RH is the model's input | RH depends on T, so mapping both double-counts the temperature error and breaks the diurnal coupling |
| Wet bulb directly | Towers run on it | Not a model input; T and RH can't be recovered from it |

Pressure is not corrected (no estimate uses it). No corrected hour has Td above T, and RH tops out at 100%; a test holds
the package to it. (The raw Open-Meteo copy has about 8 hours per cell, out of 263,000, where Td is above T by its 0.05 C
steps. RH is clipped there, as now, and those cells are uncorrected.)

### 2. Quantile scheme

- **Empirical, not parametric.** Thirty years give about 8,000 hours a bin at the resolution below, enough for 99 empirical
  quantiles. T is skewed in summer, and D is bounded at 0 and heavy-tailed in dry spells. A normal or gamma fit misplaces
  exactly the tails that the design dry-bulb and the peak day read.
- **Additive deltas** for both T and D, read at each hour's own quantile of its ERA5 bin and held constant beyond the 1st
  and 99th percentiles.
- **By calendar month, fitted on that month and the months either side**, not by season: lake breezes and coastal fog shift
  between May and September faster than a three-month season resolves.
- **By 3-hour block of local standard time** (8 blocks), not every hour: the shore bias is largest on summer afternoons,
  so time of day matters. Hourly bins would leave a third as many hours per bin.
- 96 bins, 99 quantiles each. Fitting and applying a cell takes under half a second.

### 3. Which stations anchor it

Every station that passes the snapshots' rule (85% of hours with temperature and dew point over 1995-2024, the same screens
and gap filling: `climate.screened_hourly`) qualifies if it is in the four states or within 100 km of a place in them:

| Source | Candidates | Qualify | Shore stations |
|---|---|---|---|
| ISD, one ID spanning 1995-2024 (`climate.isd_stations`, the snapshots' set) | 132 | 88 | 20 |
| ISD linked across a change of ID (`climate.isd_sites`) | 66 | 13 | 2 |
| ECCC hourly (`climate.eccc_sites`) | 9 | 5 | 5 |
| **All** | **207** | **106** | **27** |

- **Linking ISD (decision 3a).** Pieces that share a USAF or a WBAN number and stand within 5 km of each other are one site.
  Between them they must cover 85% of the days, the newest must run to the end of the period, and one must have a WBAN.
  The usual case is a USAF number under WBAN 99999 until 2005 and its own WBAN from 2006 (Lorain County Regional,
  725214-99999 then 725214-04849). An hour that two pieces both report is taken from the newer. The rule rejects pieces
  more than 5 km apart even when they share a USAF: Austin's 722540 is Camp Mabry before 1998 and Bergstrom after.
  Of the 66 linked candidates, 53 fail the 85% rule, mostly AWOS pieces without dew point. The 13 that pass are
  Lorain County and Newport News, the two near shore, plus Austin-Bergstrom, Austin-Camp Mabry, Stinson, Denton, Fort
  Stockton, Lima, Defiance, Metcalf Field, Mercer County WV, York PA and Frederick OK. Each has 2-6 poor years (under 85% of
  hours) left out, mostly at the start of the period. The snapshots' station set (`isd_stations`) is unchanged.
- **ECCC (decision 3b).** The records come from Environment and Climate Change Canada's hourly climate data, read from
  MSC GeoMet (api.weather.gc.ca, collection `climate-hourly`), under the ECCC Data Servers End-use Licence, version 2.1.
  The licence is open: copying, adapting and redistributing are allowed, commercial use included, with attribution and
  no implied endorsement. The attribution is "Contains information licenced under the Data Server End-use Licence of
  Environment and Climate Change Canada." (`climate.ECCC_ATTRIBUTION`).
  - **Which licence.** The climate.weather.gc.ca site links an older "limited use" agreement, which asks for permission
    for uses it doesn't name. The records are read through GeoMet, where the End-use Licence applies.
  - **Linking.** ECCC gives a station a new Climate ID when it changes hands or goes automatic and keeps no number across
    the change. Pieces are linked when they stand within 5 km and share the first word of their names (Windsor A has
    three IDs, Sarnia four).
  - **What is kept.** A value flagged missing ("M") is left out, and other flags are kept, as ISD-Lite keeps them.
  - **Screening.** It is ISD's: the neighbors that can overrule a suspect hour are ISD stations within 150 km.
  - **Who qualifies.** Windsor A, Sault Ste. Marie, Gore Bay, Goderich and Thunder Bay. Caribou Island, Welcome Island
    and Long Point (automatic lighthouse stations) fail.
  - **Sarnia fails too, at 79.8% of hours.** Sarnia Airport reported 43% of hours from 1995 to 2004, a part-time
    daytime schedule, and the linked record only becomes whole in 2006. So Sarnia can't anchor Port Huron under the
    rule.
- **Distance limit 100 km** from the cell's center, at most 4 stations, weighted 1/d^2 (d at least 5 km).
- **Elevation.** Each station's temperature quantiles are moved to the target cell's ERA5 elevation at 6.5 C per km.

### 4. Which cells, and from which stations

The correction is computed **per cell, at the cell's center**, not per place, so every place in a cell keeps the same
weather and the runs stay one per cell (1,233). The stations' quantiles are averaged and the cell mapped onto them, each
station's temperature moved to the cell's elevation (the prototype's "lapse" way; "bias" and "target" did worse, below).

- **Cells under 90% land** (decision 1): 126 cells, 777 places.
- **From shore stations only** (decision 2). A station is a shore station when its own cell under the land rule is under
  90% land.
  - **Why the cell test.** It is the same test the cells get, so a station anchors shore cells exactly when a place at
    the station would be corrected. It needs only the land-sea mask already in use, and it is reproducible.
  - **Why not distance from the shoreline.** A distance needs a shoreline dataset and a second threshold, and it would
    count an airport 3 km behind a dune and one 3 km from a bay alike.
  - **Its edges.**
    - A large inland lake makes a shore cell: Roscommon County (Houghton Lake) is 0.89, and Detroit City and Detroit
      Metro are 0.88 (Lake St. Clair, the Detroit River).
    - A station on the water can sit in a cell that is mostly land: Corpus Christi NAS, on the bay, is in a cell 0.96
      land.
- **A shore cell with no shore station within 100 km stays uncorrected**, and its file and each of its places' notes say
  so.

| Station set | Shore cells corrected | Places corrected | Places left uncorrected |
|---|---|---|---|
| Proposal of Nov 4: any station, ISD only | 110 | 711 | 66 |
| Shore stations, ISD only | 90 | 601 | 176 |
| + linked ISD | 90 | 601 | 176 |
| **+ ECCC (decided)** | **94** | **619** | **158** |

- **Linking adds no cells.** Its two shore stations, Lorain County and Newport News, stand where shore stations were
  already near. It changes which stations anchor cells, not how many cells, and it matters where a nearby station is
  held out (Lorain and Cleveland, below).
- **ECCC adds 4 cells and 18 places**, all in Michigan:
  - the Thumb's Lake Huron shore (Sandusky, Harbor Beach and 14 townships in Sanilac and Huron counties), from Goderich,
    across the lake;
  - Isle Royale's two townships, from Thunder Bay.
  Elsewhere it adds Windsor A and the Ontario Sault to cells that already had a shore station. In the build, Port Huron's own
  cell is corrected from Detroit City (78 km) and Windsor A (88 km), and from Windsor A alone when Detroit City is held out
  (below).
- **Corrected under the decided rule:** Michigan 353 of 462 shore places, Ohio all 172, Virginia all 56, Texas 38 of 87.
- **Uncorrected (158 places in 32 cells):**
  - Michigan: Lake Michigan's southwest shore (Benton Harbor, St. Joseph, Coloma; Chicago Midway and Muskegon are just
    over 100 km), the Thumb and Saginaw Bay (Caseville, Bad Axe, Essexville), and the Upper Peninsula's south and Lake
    Superior shores (Escanaba, Menominee, Manistique, Munising, Marquette, whose airport fails the 85% rule).
  - Texas: Galveston Bay and the Gulf shore (Galveston, Dickinson, Freeport, Corpus Christi, Port Isabel, South Padre
    Island). Galveston's airport fails the 85% rule, Corpus Christi's and Brownsville's sit in cells at least 96% land, and
    Palacios and Beaumont are over 100 km away.
  - Under the proposal most of these were corrected from inland stations. On the checks below, that is where the
    corrections overshot.

### 5. Overlap period and trends

- **The overlap is the run period, 1995-2024.** Each station's quantiles are fitted on its own kept hours, and its cell's
  ERA5 quantiles on the same hours, so a station's missing years don't bias the pair.
- **Trends are ERA5's.** The mapping is fitted on all 30 years pooled and preserves each hour's rank in its bin, so the
  corrected series keeps ERA5's year-to-year sequence and trend (tested). At the first 88 stations, ERA5's trend in
  annual mean T is within 0.06 C per decade of the stations' (median; 10-90% of stations -0.25 to +0.13), and Td within
  0.01. The 0.4% dry-bulb rose 0.60 C (stations) and 0.70 C (cells) from 1995-2009 to 2010-2024 (medians). No
  detrending. A trend-preserving variant (quantile delta mapping, Cannon et al. 2015) matters for projections, not for a
  historical period corrected against itself.

### 6. In the snapshot and the methods notes

- **Cell file** (`cells/<cell>.json`, format 3 of 0004) gains `correction`:
  - `method` ("qm-1");
  - `applied` (true or false);
  - `reason`: "cell under 90% land", "cell at least 90% land" or "no shore station within 100 km";
  - `stations`: id, name, source, km, weight and elevation;
  - the change it made to the design dry-bulb, the mean summer afternoon T and the mean dew point, before and after.
- **`places.json`**: each place gains `weather_corrected`.
- **`manifest.json`**: the method and its version, and the anchor list with each station's source and fetch dates. It
  also records the ISD citation, and the ECCC licence and attribution (`ECCC_ATTRIBUTION`, `ECCC_LICENCE`) wherever a
  Canadian station is used.
- **The R2 raw cache** keeps the anchors' quantile tables (about 8 MB for 106 stations), so a rebuild reproduces every
  correction without refetching ISD or ECCC.
- **Each place's methods note** says one of:
  - "ERA5 at cell X (62% land), corrected toward Lorain County Regional (23 km) for the lake's effect";
  - "ERA5 at cell X (68% land), not corrected: no shore station within 100 km";
  - "ERA5 at cell X, at least 90% land, not corrected".
  The site credits ECCC where a Canadian station is named.

## Prototype

Two checks, both leaving one station out, rerun on Nov 4 under the decisions.

### At every anchor station, on the weather alone

Each of the 106 stations was held out in turn, along with any other within 5 km of it. Its cell was corrected from the
stations left, and the corrected cell was compared with the station on the station's own hours
([cv_weather.py](../methods/qm-check/cv_weather.py)). 80 stations have another within 100 km.

The figures are median absolute error (mean error) in C. A way that can't correct a station (no station near enough)
counts it uncorrected.

| Stations | Way | Design dry-bulb | 0.4% wet bulb | Summer afternoon T | Mean dew point |
|---|---|---|---|---|---|
| The 16 shore stations the decided rule corrects | none | 1.18 (-1.34) | 0.22 (-0.24) | 0.59 (-0.76) | 0.42 (+0.51) |
| | lapse, any station (proposal) | 0.28 (+0.05) | 0.33 (+0.24) | 0.28 (+0.24) | 0.18 (-0.12) |
| | lapse, shore stations, ISD only | 0.29 (-0.18) | 0.18 (+0.19) | 0.39 (+0.03) | 0.19 (+0.02) |
| | **lapse, shore stations, all (decided)** | **0.23 (-0.04)** | 0.28 (+0.25) | 0.31 (+0.11) | **0.16 (-0.07)** |
| Cells at least 90% land (60) | **none (decided)** | **0.42 (-0.24)** | 0.18 (-0.06) | **0.33 (-0.14)** | 0.23 (+0.08) |
| | bias | 0.48 (+0.08) | 0.19 (+0.07) | 0.39 (+0.11) | 0.26 (-0.06) |
| | lapse | 0.45 (-0.15) | 0.22 (-0.02) | 0.37 (-0.05) | 0.27 (-0.06) |

The other ways tried (bias, target, nearest station only, 50 km, by station set) are in
[cv_weather.json](../methods/qm-check/cv_weather.json). The table of every station is printed by
[summarize_weather.py](../methods/qm-check/summarize_weather.py).

- **On land cells no correction beats ERA5 as it is,** with 106 stations as with 88. That is decision 1's footing.
- **On shore cells, shore stations only takes out the overshoot.** The proposal (any station) ran warm where the only
  near stations are inland. Under the decided rule those cells stay uncorrected: Palacios (+3.0 C under the proposal),
  Muskegon (+1.4 C) and Erie (+1.0 C). The mean design dry-bulb error goes from +0.05 to -0.04 C and the median from
  0.28 to 0.23.
- **The 0.4% wet bulb still rises** by about 0.3 C on average where cells are corrected: Newport News +1.0 C, Oceana
  +0.8 C, Sault Ste. Marie (Ontario) +0.8 C. Matching T and D separately gets each margin right but not how often hot
  hours are also humid ones. Towers run on the wet bulb, and they move 2% or less (below).

### The 21 places, through the cooling model

Each place's cell (the land rule's) was corrected without its reference station and run as the station check is
(model 1.7, 400 draws, seed 7, per 100 MW; [cv_places.py](../methods/qm-check/cv_places.py)). The 16 places on cells at
least 90% land are not corrected under decision 1, so they are as they were: hybrid average within 3% of their stations
(median) and assist within 5%.

The five shoreline places, median absolute difference from the station (mean):

| Way | Towers avg | Towers peak | Hybrid avg | Hybrid peak | Assist avg | Assist peak |
|---|---|---|---|---|---|---|
| none | 0% (-0%) | 0% (-1%) | 10% (-15%) | 6% (+5%) | 35% (-34%) | 22% (-19%) |
| lapse, any station (proposal) | 0% (+0%) | 1% (+0%) | 10% (-2%) | 4% (+0%) | 4% (-7%) | 2% (-6%) |
| lapse, shore stations, ISD only | 0% (-0%) | 0% (-1%) | 8% (-12%) | 4% (+4%) | 27% (-23%) | 16% (-13%) |
| lapse, shore stations, + linked ISD | 0% (-0%) | 1% (-0%) | 4% (-7%) | 4% (+1%) | 4% (-13%) | 2% (-6%) |
| **lapse, shore stations, + ECCC (decided)** | 0% (-0%) | 1% (+0%) | **5% (-4%)** | **3% (+1%)** | **7% (-8%)** | **3% (-3%)** |

One by one, against their stations: uncorrected, then the proposal, then decided.

| Place | Cell land | Shore stations used (km) | Hybrid avg | Hybrid peak | Assist avg | Assist peak | Design dry-bulb |
|---|---|---|---|---|---|---|---|
| Virginia Beach, VA | 0.51 | Norfolk Intl 24, Norfolk NAS 33, Newport News 61 | -10 / +4 / +5% | +8 / +4 / +4% | -44 / +1 / +2% | -30 / +0 / -0% | -3.0 / +0.3 / +0.3 C |
| Lorain, OH | 0.59 | Lorain County Regional 23 | -8 / +18 / +4% | +18 / +4 / +5% | -35 / +12 / -4% | -22 / +1 / -2% | -2.4 / +0.6 / -0.0 C |
| Cleveland, OH | 0.65 | Lorain County Regional 40 | -11 / +10 / -0% | +4 / -2 / -0% | -27 / +4 / -7% | -16 / -4 / -3% | not run |
| Port Huron, MI | 0.75 | Windsor A 88 (ECCC) | -39 / -39 / -21% | -6 / -6 / -3% | -52 / -52 / -25% | -23 / -23 / -7% | -2.0 / -2.0 / -0.4 C |
| Toledo, OH | 0.78 | Detroit Metro 55, Windsor A 74, Detroit City 84 | -6 / -1 / -7% | +1 / +1 / +1% | -11 / -2 / -9% | -6 / -2 / -3% | -0.5 / -0.3 / -0.6 C |

- **Lorain and Cleveland no longer overshoot.** With Cleveland-Hopkins held out, their only shore station is Lorain County
  Regional, a linked ISD record. On ISD alone (one ID) they'd have none and stay uncorrected. The hybrid average comes
  to +4% and -0%, against +18% and +10% when corrected from Akron-Canton.
- **Port Huron is now corrected,** with its own reference (Detroit City, 80 km) held out, from Windsor A, 88 km away.
  Its gap halves: hybrid average -39% to -21%, assist -52% to -25%, and the design dry-bulb -2.0 C to -0.4 C. Detroit
  City is 80 km from Port Huron's cell and its own cell is 0.88 land. So the station check can't say how far a Port Huron
  shore record would be from either. Sarnia, 10 km away, fails the 85% rule (section 3).
- **Toledo** is corrected from the Detroit stations and Windsor A rather than from its inland neighbors. It's slightly
  further from Toledo Express on the average days (-7% and -9%) than under the proposal (-1% and -2%), and well within
  the station-to-station scatter.
- **Towers move 2% or less** everywhere, corrected or not.
- **Mass and energy balance.** The correction is outside the model, and the model's balance tests pass unchanged. The
  corrected weather is physical: no corrected hour at any of the five has Td above T, and RH stays at or below 100%.
  `tests/test_quantile_mapping.py` holds the package to both and to the leave-one-out results above.

## Release fit

**Decided: in model 1.8 with ERA5.**

- **One change in the numbers, not two.** Model 1.8 already changes every place's weather.
- **The same build.** The correction runs before the cooling run and takes under half a second per cell. 94 cells are
  corrected, and the run count (1,233 cells, about 26 hours at six workers) doesn't change.
- **Added work outside the runs**, measured on Nov 4:
  - qualifying the 207 candidate stations: ISD-Lite and ECCC downloads, 10 minutes at eight workers with the first 88
    stations cached;
  - fetching ERA5 at the 16 added stations' own cells: 141 s;
  - the leave-one-out weather check: 94 s.

## Open, for Andrew

- **The wet bulb.** The 0.4% wet bulb rises about 0.3 C where cells are corrected. Towers barely move, but a joint
  correction (T and D mapped together, or the wet bulb checked after mapping) would be the next refinement.
- **Sarnia.** Under the 85% rule its part-time 1995-2004 record keeps it out. Over 2006-2024 alone it is whole.
- **Across the lake.** Goderich corrects the Thumb's Lake Huron shore from 83-88 km away, across the water. It
  is a shore station on the same lake, but on its east side.
- **The cell test's edges.** It counts inland-lake stations as shore stations (Roscommon County, the Detroit stations; all
  0.88-0.89, none overshooting on the check), and it misses stations on the water in mostly-land cells (Corpus Christi
  NAS).
- **The 158 uncorrected shore places** (Benton Harbor, Saginaw Bay, the Upper Peninsula's shores, Galveston Bay, Corpus
  Christi). More stations would come from ISD sites whose record starts after 1995 under one ID, which the 85% rule's
  span test excludes. Coastal stations (NOAA C-MAN, buoys) report temperature but rarely dew point.
- **Valley and ridge cells** (Roanoke, 14-22% low on land): not addressed. A terrain covariate would be a later step.

## Short note for the methods pages (decided Nov 4, 2026, for model 1.8)

> **Correction near lakes and the sea.** Where a place's ERA5 cell is partly water (under 90% land), its hourly
> temperature and dew point are corrected toward the weather stations near the shore within 100 km. Those are NOAA's
> airport stations, and Environment and Climate Change Canada's in Ontario. The correction works month by month and by
> time of day, so the cell's distribution matches the stations' at the cell's own elevation. ERA5's day-to-day weather and
> trends are kept, and the dew point never passes the temperature. Stations inland of the shore are not used, and a
> shore cell with none near is left as ERA5 gives it. On land cells ERA5 is used as it is, since held-out stations
> showed it to be as close as any correction. Each place's note names the stations used, or says why the cell was not
> corrected. Canadian station data: contains information licenced under the Data Server End-use Licence of Environment
> and Climate Change Canada.

## References

- Cannon, A. J., Sobie, S. R. and Murdock, T. Q. (2015). Bias correction of GCM precipitation by quantile mapping: how well
  do methods preserve changes in quantiles and extremes? Journal of Climate 28(17): 6938-6959. doi:10.1175/JCLI-D-14-00754.1.
- Maraun, D. (2016). Bias correcting climate change simulations: a critical review. Current Climate Change Reports 2(4):
  211-220. doi:10.1007/s40641-016-0050-x.
- Themeßl, M. J., Gobiet, A. and Leuprecht, A. (2011). Empirical-statistical downscaling and error correction of daily
  precipitation from regional climate models. International Journal of Climatology 31(10): 1530-1544. doi:10.1002/joc.2168.
- Hersbach, H., et al. (2020). The ERA5 global reanalysis. QJRMS 146(730): 1999-2049. doi:10.1002/qj.3803.
- NOAA NCEI Integrated Surface Database, ISD-Lite, 1995-2024, and isd-history.csv (station IDs and periods), fetched Oct 29
  and Nov 4, 2026.
- Environment and Climate Change Canada, Historical Climate Data, hourly observations, via MSC GeoMet-OGC-API
  (api.weather.gc.ca, collection climate-hourly), and the Station Inventory (Sep 30, 2026 edition), fetched Nov 4, 2026.
  Licence: Environment and Climate Change Canada Data Servers End-use Licence, version 2.1
  (https://eccc-msc.github.io/open-data/licence/readme_en/).
- Alduchov, O. A. and Eskridge, R. E. (1996). Improved Magnus form approximation of saturation vapor pressure. Journal of
  Applied Meteorology 35(4): 601-609.
