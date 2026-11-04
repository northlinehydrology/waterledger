# 0005: Quantile mapping ERA5 to stations

Status: **proposed, Nov 4, 2026; prototyped, not built.** Andrew asked for it on Nov 3 ("Let's do the quantile mapping") after
the land rule of [0004](0004-era5-weather.md) (decision 3) turned out to move only the mostly-water cells. He leads the
method; this note gives the choices, a recommendation for each and a prototype on the station check's 21 places. Nothing here
changes a model, parameter or snapshot. Scripts and results are in [docs/methods/qm-check/](../methods/qm-check/).

## The problem

On the station check, ERA5's cells that are part lake or sea run cool next to the shore airports. After the land rule, 777
places still sit on cells 50-90% land (Michigan 462, Ohio 172, Virginia 56, Texas 87). At the check's five shoreline places
the uncorrected cell is 15% low on the hybrid average day and 34% low on assist (means against the nearest station),
with design dry-bulbs 2-3 C low. Inland, ERA5 is already within the scatter between stations.

## Choices and recommendations

### 1. What to correct

| Option | For | Against |
|---|---|---|
| **T and the dew-point depression D = T - Td** (recommended) | D at or above 0 after correction gives Td at or below T and RH at or below 100% by construction; T and D keep ERA5's own hour-to-hour timing | Corrects two margins, not their joint distribution |
| T and Td separately, then Td clipped to T | Simplest | Clipping makes saturated hours that neither record has |
| T and RH | RH is the model's input | RH depends on T, so mapping both double-counts the temperature error and breaks the diurnal coupling |
| Wet bulb directly | Towers run on it | Not a model input; T and RH can't be recovered from it |

Pressure is not corrected (no estimate uses it). The prototype's corrected series have no hour with Td above T and RH tops
out at 100%. (The raw Open-Meteo copy has about 8 hours per cell, out of 263,000, where Td is above T by its 0.05 C steps; RH is
clipped there, as now.)

### 2. Quantile scheme

- **Empirical, not parametric** (recommended). Thirty years give about 8,000 hours a bin at the resolution below, enough
  for 99 empirical quantiles. T is skewed in summer and D is bounded at 0 and heavy-tailed in dry spells; a normal or gamma
  fit misplaces exactly the tails the design dry-bulb and the peak day read.
- **Additive deltas** for both T and D, read at each hour's own quantile of its ERA5 bin and held constant beyond the 1st
  and 99th percentiles.
- **By calendar month, fitted on that month and the months either side** (recommended), not by season: lake breezes and
  coastal fog shift between May and September faster than a three-month season resolves.
- **By 3-hour block of local standard time** (8 blocks), not every hour: the shore bias is largest on summer afternoons,
  so time of day matters. Hourly bins would leave a third as many hours per bin.
- 96 bins, 99 quantiles each. Fitting and applying a cell takes under half a second.

### 3. Which stations anchor it

- **Every ISD station that passes the snapshots' rule** (`climate.isd_hourly`: a record spanning 1995-2024 under one ID,
  85% of hours with temperature and dew point, the same screens and gap filling), in the four states or within 100 km of a
  place in them: 88 of 132 candidates (Texas 28, Michigan 14, Virginia 10, Ohio 9, and 27 in neighboring states).
- **Distance limit 100 km** from the cell's center, at most 4 stations.
- **Elevation**: no hard limit. Each station's temperature quantiles are moved to the target cell's ERA5 elevation at
  6.5 C per km (the "lapse" way below), which is what made the shore results work. Valley airports such as Roanoke stay a
  known limit (below).
- The network is thin: 30 of the 88 have no other qualifying station within 100 km, and Austin, Houston and Port Huron have
  none left once their own station is held out. Linking ISD records across a change of station ID by WBAN (option A of the
  Oct 29 check) would add stations; it is the first thing to do if more anchors are wanted.

### 4. Places between stations

The correction is computed **per cell, at the cell's center**, not per place, so every place in a cell keeps the same
weather and the runs stay one per cell (1,233). Three ways of carrying it were tested:

- **"bias"**: average the stations' own cell biases (station minus its cell) and add them to the target cell. It assumes
  ERA5's error is smooth in space. It fails at the shore: a shore airport's neighbors sit on land cells with a different
  bias.
- **"target"**: average the stations' quantiles and map the target cell onto them. It assumes the true climate is smooth.
- **"lapse"**: "target" with each station's temperature moved to the target cell's elevation.

Weights are 1/d^2 (d at least 5 km). **What a cell far from any station gets: nothing.** It keeps ERA5 as it is, and its
file says so.

**Recommendation: correct only cells under 90% land, by "lapse"; leave cells at least 90% land as ERA5 gives them.** On land
cells no way of carrying beat ERA5 uncorrected at the held-out stations (below), so a correction there only adds the
station-to-station scatter. In the four states this corrects 110 cells (711 places) and leaves 16 shore cells (66 places,
mostly Michigan's Upper Peninsula and islands) uncorrected for want of a station.

### 5. Overlap period and trends

- **The overlap is the run period, 1995-2024.** Each station's quantiles are fitted on its own kept hours, and its cell's
  ERA5 quantiles on the same hours, so a station's missing years don't bias the pair.
- **Trends are ERA5's.** The mapping is fitted on all 30 years pooled and preserves each hour's rank in its bin, so the
  corrected series keeps ERA5's year-to-year sequence and trend. At the 88 stations, ERA5's trend in annual mean T is
  within 0.06 C per decade of the stations' (median; 10-90% of stations -0.25 to +0.13), and Td within 0.01. The 0.4%
  dry-bulb rose 0.60 C (stations) and 0.70 C (cells) from 1995-2009 to 2010-2024 (medians). No detrending is proposed. A
  trend-preserving variant (quantile delta mapping, Cannon et al. 2015) matters for projections, not for a historical
  period corrected against itself.

### 6. In the snapshot and the methods notes

- **Cell file** (`cells/<cell>.json`, format 3 of 0004) gains `correction`: `method` ("qm-1"), `applied` (true or false),
  `reason` ("cell under 90% land", "cell at least 90% land" or "no station within 100 km"), `stations` (id, name, km,
  weight, elevation), and the change it made: design dry-bulb, mean summer afternoon T and mean dew point, before and after.
- **`places.json`**: each place gains `weather_corrected`.
- **`manifest.json`**: the method and its version, the anchor list with ISD fetch dates, and the ISD citation.
- **The R2 raw cache** keeps the anchors' quantile tables (about 7 MB for 88 stations), so a rebuild reproduces every
  correction without refetching ISD.
- **Each place's methods note** says either "ERA5 at cell X (62% land), corrected toward Cleveland-Hopkins (16 km) and
  Akron-Canton (70 km) for the lake's effect", or "ERA5 at cell X, not corrected", with the reason.

## Prototype

Two checks, both leaving one station out.

### At every anchor station, on the weather alone

Each of the 88 stations was held out in turn, along with any other within 5 km of it. Its cell was corrected from the
stations left, and the corrected cell was compared with the station on the station's own hours
([cv_weather.py](../methods/qm-check/cv_weather.py)). 58 stations have another within 100 km. The figures are median
absolute error (mean error) in C:

| Cells | Way | Design dry-bulb | 0.4% wet bulb | Summer afternoon T | Mean dew point |
|---|---|---|---|---|---|
| Under 90% land (15) | none | 1.21 (-1.16) | 0.24 (-0.23) | 0.59 (-0.68) | 0.37 (+0.47) |
| | bias | 1.39 (-0.57) | 0.29 (+0.06) | 0.78 (-0.25) | 0.50 (+0.19) |
| | target | 0.60 (+0.32) | 0.40 (+0.23) | 0.35 (+0.45) | 0.30 (-0.24) |
| | **lapse** | **0.30 (+0.40)** | 0.34 (+0.31) | **0.32 (+0.54)** | **0.28 (-0.15)** |
| At least 90% land (43) | **none** | **0.40 (-0.19)** | 0.19 (-0.05) | **0.35 (-0.13)** | 0.22 (+0.10) |
| | bias | 0.47 (+0.04) | 0.19 (+0.06) | 0.45 (+0.06) | 0.30 (-0.06) |
| | target | 0.50 (+0.01) | 0.21 (+0.14) | 0.51 (+0.10) | 0.40 (+0.08) |
| | lapse | 0.44 (-0.18) | 0.21 (-0.04) | 0.42 (-0.09) | 0.33 (-0.11) |

More variants (nearest station only, 50 km) are in [cv_weather.json](../methods/qm-check/cv_weather.json) and did no
better. On shore cells "lapse" cuts the design dry-bulb error by three-quarters but overshoots on average (+0.40 C), and it
raises the 0.4% wet bulb: Muskegon +1.5 C, Erie +1.2 C. Palacios, on the Texas coast, goes 3.0 C too warm, because its
neighbors are inland and the coast there really is cooler.

### The 21 places, through the cooling model

Each place's cell (the land rule's) was corrected without its reference station and run as the station check is
(model 1.7, 400 draws, seed 7, per 100 MW; [cv_places.py](../methods/qm-check/cv_places.py)). The figures are median
absolute difference from the station (mean); "shore" is the recommendation (lapse under 90% land, none otherwise):

| Places | Way | Towers avg | Towers peak | Hybrid avg | Hybrid peak | Assist avg | Assist peak |
|---|---|---|---|---|---|---|---|
| The five shoreline | none | 0% (-0%) | 0% (-1%) | 10% (-15%) | 6% (+5%) | 35% (-34%) | 22% (-19%) |
| | bias | 0% (-0%) | 0% (-1%) | 10% (-13%) | 6% (+6%) | 30% (-29%) | 16% (-15%) |
| | **lapse = shore** | 0% (+0%) | 1% (+0%) | 10% (-2%) | 4% (+0%) | **4% (-7%)** | **2% (-6%)** |
| The other 16 | **none = shore** | 0% (-0%) | 1% (-0%) | **3% (+1%)** | 2% (-1%) | **5% (+1%)** | 4% (-2%) |
| | bias | 0% (-0%) | 1% (-1%) | 4% (-0%) | 2% (-1%) | 6% (-0%) | 4% (-3%) |
| | lapse | 0% (-0%) | 1% (-0%) | 4% (-1%) | 2% (-1%) | 6% (-0%) | 5% (-3%) |

The shoreline places one by one, against their stations (uncorrected, then lapse):

| Place | Cell land | Anchors (km) | Hybrid avg | Hybrid peak | Assist avg | Assist peak | Design dry-bulb |
|---|---|---|---|---|---|---|---|
| Lorain, OH | 0.59 | Akron-Canton 80 | -8% to +18% | +18% to +4% | -35% to +12% | -22% to +1% | -2.4 to +0.6 C |
| Virginia Beach, VA | 0.51 | Norfolk Intl 24, Norfolk NAS 33 | -10% to +4% | +8% to +4% | -44% to +1% | -30% to +0% | -3.0 to +0.3 C |
| Cleveland, OH | 0.65 | Akron-Canton 70, Youngstown 94 | -11% to +10% | +4% to -2% | -27% to +4% | -16% to -4% | not run |
| Port Huron, MI | 0.75 | none within 100 km | -39% (unchanged) | -6% | -52% | -23% | -2.0 C |
| Toledo, OH | 0.78 | Detroit City 55 and three more | -6% to -1% | +1% to +1% | -11% to -2% | -6% to -2% | -0.5 to -0.3 C |

- **Assist and the peak days come right at the shore.** Assist's average-day gap closes from about a third low to within
  12% at all four corrected places, and every peak day is within 4%.
- **The hybrid average day overshoots where the only anchors are inland.** Lorain (+18%) and Cleveland (+10%) are corrected
  toward Akron-Canton, 70-80 km inland and about 140-170 m above the two cells. The lapse rate takes out the height, but not the lake's absence.
  Where a shore station is near (Virginia Beach, Toledo), the hybrid average comes within 5%.
- **Port Huron is not corrected:** with Detroit City held out, no station is within 100 km. 66 places are like it.
- **Towers move 2% or less** everywhere, corrected or not.
- **Mass and energy balance:** the correction is outside the model. The model's balance tests pass unchanged (401 passed),
  and the corrected weather is physical (Td at or below T, RH at or below 100%, every hour).

## Release fit

**Recommendation: ship it in model 1.8 with ERA5, if Andrew accepts the method as it stands.**

- **One change in the numbers, not two.** Model 1.8 already changes every place's weather. Releasing an uncorrected 1.8
  would publish shore numbers the check shows are a third low for assist, and change them again weeks later.
- **The same build.** The correction runs before the cooling run, under half a second per cell, and only 110 cells are
  corrected. The run count (1,233 cells, about 26 hours at six workers) doesn't change. Added work outside the runs:
  qualifying the 88 anchor stations (ISD downloads, once; not timed, with 59 of the 132 candidates not yet cached) and
  fetching ERA5 at their cells (80 cells beyond the places' own, about 11 minutes from the open copy).
- **As its own model version (1.9) instead,** only the 110 corrected cells would rerun (about 2.4 hours), the other cells'
  results being unchanged. This is the better route if Andrew wants more anchors first (the WBAN linking above) or a
  different handling of shore cells whose only anchors are inland.

## Open, for Andrew

- **The 90% threshold.** It is where the held-out stations stop gaining from correction, read from 15 shore and 43 land
  stations; it is a judgment, not a fit.
- **Shore cells with only inland anchors** (Lorain, Cleveland): accept the overshoot, require a shore anchor (land under
  0.9) among the stations used, or weight anchors by how alike their cells' land fractions are. The last two would leave
  more cells uncorrected.
- **More anchors** from WBAN-linked records, and whether to admit Canadian stations (Sarnia for Port Huron, Thunder Bay for
  Isle Royale's Ontario cells) from Environment and Climate Change Canada.
- **Valley and ridge cells** (Roanoke, 14-22% low on land): not addressed; a terrain covariate would be a later step.

## Short note for the methods pages (draft, if it ships)

> **Correction near lakes and the sea.** Where a place's ERA5 cell is partly water (under 90% land), its hourly
> temperature and dew point are corrected toward the NOAA airport stations within 100 km, month by month and by time of
> day, so the cell's distribution matches theirs at the cell's own elevation. ERA5's day-to-day weather and trends are
> kept. On land cells ERA5 is used as it is, since held-out stations showed it to be as close as any correction. Each
> place's note names the stations used, or says the cell was not corrected and why.

## References

- Cannon, A. J., Sobie, S. R. and Murdock, T. Q. (2015). Bias correction of GCM precipitation by quantile mapping: how well
  do methods preserve changes in quantiles and extremes? Journal of Climate 28(17): 6938-6959. doi:10.1175/JCLI-D-14-00754.1.
- Maraun, D. (2016). Bias correcting climate change simulations: a critical review. Current Climate Change Reports 2(4):
  211-220. doi:10.1007/s40641-016-0050-x.
- Themeßl, M. J., Gobiet, A. and Leuprecht, A. (2011). Empirical-statistical downscaling and error correction of daily
  precipitation from regional climate models. International Journal of Climatology 31(10): 1530-1544. doi:10.1002/joc.2168.
- Hersbach, H., et al. (2020). The ERA5 global reanalysis. QJRMS 146(730): 1999-2049. doi:10.1002/qj.3803.
- NOAA NCEI Integrated Surface Database, ISD-Lite, 1995-2024.
- Alduchov, O. A. and Eskridge, R. E. (1996). Improved Magnus form approximation of saturation vapor pressure. Journal of
  Applied Meteorology 35(4): 601-609.
