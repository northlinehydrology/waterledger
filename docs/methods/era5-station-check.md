# ERA5 at each place's nearest cell, against the stations: the station check on model 1.7

Working note (Nov 3, 2026), for the methods appendix and the ERA5 plan ([design 0004](../design/0004-era5-weather.md)). It reruns
[station-distance-check.md](station-distance-check.md) (Oct 29, model 1.2) on model 1.7 and adds ERA5 at each place's nearest
0.25-degree cell. Nothing in the models, parameters or published snapshots was changed for it. Scripts and results are in
[era5-check/](era5-check/).

## Question

Andrew decided on Nov 1, 2026 that every place takes its cooling weather from its nearest ERA5 cell. Before the build: at the
places where the station choice mattered on Oct 29, how does ERA5 at the place's own cell compare with the nearest qualifying
station, and with what is published now?

## Method

- **Places.** The 21 of the Oct 29 check: 13 where a nearer qualifying station exists and 8 where the published station is
  already the nearest. Each at its Census internal point, from the 2026-11-02.2 snapshots.
- **Published.** The p50 in the 2026-11-02.2 snapshot (model 1.7) for the place's division station, or for Michigan, its region
  point (Open-Meteo best match). One was rerun from its station record (Ohio division 1, Findlay) and matched the snapshot in
  every statistic, so the runs here and the snapshots agree.
- **Nearest qualifying station.** Searched from the place's own point with the snapshots' rule (an ISD station spanning
  1995-2024 under one ID, at least 85% of hours with temperature and dew point, the same screens and gap filling:
  `waterledger_data.climate.isd_hourly`).
- **ERA5.** The cell nearest the place (latitude and longitude rounded to 0.25 degree), hourly 2 m temperature and dew point,
  1995-2024, from Open-Meteo's open-data copy of Copernicus ERA5 on AWS (stored in 0.05 C steps), moved to local standard time
  by longitude, with relative humidity from the stations' Magnus form. The cell's land share is ERA5's land-sea mask.
- **Runs.** `cooling.run_location`, model 1.7: 400 Latin hypercube draws, seed 7, per 100 MW, every design. Results are the
  p50 of cooling withdrawal (makeup water) without staff water: the average day and the 1-in-10-year peak day.

## Results

### Where the weather comes from

| Place | Published point (km) | Nearest qualifying station (km) | ERA5 cell (km, land share) |
|---|---|---|---|
| Austin city, TX | Victoria (178) | San Antonio Intl (110) | 30.25, -97.75 (5 km, 1.00) |
| San Antonio city, TX | Victoria (168) | San Antonio Intl (10) | 29.50, -98.50 (5 km, 0.99) |
| Round Rock city, TX | Fort Worth Naval Air Station Jrb/Carswell Field (250) | Waco (128) | 30.50, -97.75 (9 km, 0.97) |
| Dallas city, TX | Fort Worth Naval Air Station Jrb/Carswell Field (64) | Dallas/Ft Worth Intl (26) | 32.75, -96.75 (5 km, 0.97) |
| El Paso city, TX | Winkler County (305) | El Paso Intl (6) | 31.75, -106.50 (13 km, 1.00) |
| Amarillo city, TX | Lubbock Intl (171) | Amarillo Rick Husband Intl (10) | 35.25, -101.75 (9 km, 1.00) |
| Houston city, TX | G Bush Intercontinental Ap/Houston Ap (22) | same | 29.75, -95.50 (11 km, 1.00) |
| Lubbock city, TX | Lubbock Intl (13) | same | 33.50, -102.00 (12 km, 1.00) |
| Virginia Beach city, VA | Richmond Intl (141) | Oceana Nas (4) | 36.75, -76.00 (4 km, 0.51) |
| Bristol city, VA | Raleigh County Memorial (159) | Asheville (136) | 36.50, -82.25 (15 km, 0.98) |
| Loudoun County, VA | Washington Dulles Intl (23) | same | 39.00, -77.75 (13 km, 1.00) |
| Richmond city, VA | Richmond Intl (14) | same | 37.50, -77.50 (4 km, 0.98) |
| Roanoke city, VA | Roanoke Regional/Woodrum Field Ap (4) | same | 37.25, -80.00 (5 km, 1.00) |
| Lorain city, OH | Findlay (133) | Cleveland-Hopkins Intl (28) | 41.50, -82.25 (9 km, 0.40) |
| Toledo city, OH | Findlay (73) | Toledo Express (20) | 41.75, -83.50 (12 km, 0.78) |
| Cincinnati city, OH | Cina Muni Apt/Lukn Fd Apt (9) | same | 39.25, -84.50 (12 km, 0.99) |
| Cleveland city, OH | Cleveland-Hopkins Intl (16) | same | 41.50, -81.75 (6 km, 0.65) |
| Columbus city, OH | Port Columbus Intl (9) | same | 40.00, -83.00 (2 km, 0.99) |
| Port Huron city, MI | Ann Arbor region point (126) | Detroit City (80) | 43.00, -82.50 (5 km, 0.75) |
| Ironwood city, MI | Marquette region point (211) | Houghton County Memo Arpt (150) | 46.50, -90.25 (9 km, 0.91) |
| Gaines charter township, MI | Grand Rapids region point (11) | Gerald R Ford Intl (11) | 42.75, -85.50 (10 km, 0.98) |

#### Cooling withdrawal, average day, MGD per 100 MW (p50): published / nearest station / ERA5

| Place | Towers | ERA5 vs station | Hybrid | ERA5 vs station | Assist | ERA5 vs station |
|---|---|---|---|---|---|---|
| Austin city | 0.734 / 0.726 / 0.724 | -0% | 0.114 / 0.111 / 0.109 | -2% | 0.131 / 0.156 / 0.152 | -2% |
| San Antonio city | 0.734 / 0.726 / 0.725 | -0% | 0.114 / 0.111 / 0.110 | -1% | 0.131 / 0.156 / 0.148 | -5% |
| Round Rock city | 0.718 / 0.718 / 0.721 | +0% | 0.113 / 0.106 / 0.106 | +1% | 0.177 / 0.155 / 0.148 | -5% |
| Dallas city | 0.718 / 0.716 / 0.716 | -0% | 0.113 / 0.108 / 0.105 | -3% | 0.177 / 0.163 / 0.149 | -8% |
| El Paso city | 0.705 / 0.704 / 0.701 | -0% | 0.104 / 0.102 / 0.099 | -2% | 0.189 / 0.184 / 0.173 | -6% |
| Amarillo city | 0.688 / 0.678 / 0.680 | +0% | 0.077 / 0.063 / 0.066 | +5% | 0.126 / 0.101 / 0.102 | +1% |
| Houston city | 0.731 / 0.731 / 0.731 | +0% | 0.113 / 0.113 / 0.111 | -1% | 0.133 / 0.133 / 0.126 | -6% |
| Lubbock city | 0.688 / 0.688 / 0.688 | -0% | 0.077 / 0.077 / 0.076 | -2% | 0.126 / 0.126 / 0.119 | -5% |
| Virginia Beach city | 0.683 / 0.688 / 0.687 | -0% | 0.056 / 0.056 / 0.050 | -10% | 0.069 / 0.062 / 0.035 | -44% |
| Bristol city | 0.660 / 0.670 / 0.671 | +0% | 0.022 / 0.033 / 0.035 | +8% | 0.021 / 0.035 / 0.038 | +9% |
| Loudoun County | 0.674 / 0.674 / 0.673 | -0% | 0.048 / 0.048 / 0.045 | -5% | 0.058 / 0.058 / 0.058 | -0% |
| Richmond city | 0.683 / 0.683 / 0.684 | +0% | 0.056 / 0.056 / 0.055 | -2% | 0.069 / 0.069 / 0.068 | -1% |
| Roanoke city | 0.676 / 0.676 / 0.671 | -1% | 0.046 / 0.046 / 0.038 | -17% | 0.056 / 0.056 / 0.044 | -22% |
| Lorain city | 0.661 / 0.661 / 0.661 | -0% | 0.035 / 0.030 / 0.027 | -10% | 0.041 / 0.036 / 0.022 | -39% |
| Toledo city | 0.661 / 0.659 / 0.660 | +0% | 0.035 / 0.034 / 0.032 | -6% | 0.041 / 0.040 / 0.036 | -11% |
| Cincinnati city | 0.671 / 0.671 / 0.671 | +0% | 0.044 / 0.044 / 0.046 | +3% | 0.050 / 0.050 / 0.052 | +4% |
| Cleveland city | 0.661 / 0.661 / 0.660 | -0% | 0.030 / 0.030 / 0.027 | -11% | 0.036 / 0.036 / 0.026 | -27% |
| Columbus city | 0.667 / 0.667 / 0.665 | -0% | 0.041 / 0.041 / 0.037 | -9% | 0.048 / 0.048 / 0.041 | -15% |
| Port Huron city | 0.655 / 0.661 / 0.653 | -1% | 0.027 / 0.036 / 0.022 | -39% | 0.030 / 0.042 / 0.020 | -52% |
| Ironwood city | 0.638 / 0.635 / 0.638 | +0% | 0.012 / 0.012 / 0.017 | +41% | 0.011 / 0.011 / 0.020 | +84% |
| Gaines charter township | 0.653 / 0.655 / 0.655 | -0% | 0.026 / 0.029 / 0.028 | -3% | 0.028 / 0.032 / 0.031 | -5% |

#### Cooling withdrawal, 1-in-10 peak day, MGD per 100 MW (p50): published / nearest station / ERA5

| Place | Towers | ERA5 vs station | Hybrid | ERA5 vs station | Assist | ERA5 vs station |
|---|---|---|---|---|---|---|
| Austin city | 0.930 / 0.931 / 0.933 | +0% | 0.557 / 0.617 / 0.606 | -2% | 0.592 / 0.744 / 0.722 | -3% |
| San Antonio city | 0.930 / 0.931 / 0.926 | -0% | 0.557 / 0.617 / 0.585 | -5% | 0.592 / 0.744 / 0.684 | -8% |
| Round Rock city | 0.950 / 0.942 / 0.932 | -1% | 0.679 / 0.622 / 0.614 | -1% | 0.827 / 0.752 / 0.722 | -4% |
| Dallas city | 0.950 / 0.949 / 0.947 | -0% | 0.679 / 0.679 / 0.672 | -1% | 0.827 / 0.829 / 0.797 | -4% |
| El Paso city | 0.923 / 0.918 / 0.905 | -1% | 0.567 / 0.650 / 0.605 | -7% | 0.761 / 0.825 / 0.785 | -5% |
| Amarillo city | 0.909 / 0.891 / 0.891 | +0% | 0.597 / 0.547 / 0.555 | +1% | 0.751 / 0.689 / 0.684 | -1% |
| Houston city | 0.936 / 0.936 / 0.930 | -1% | 0.593 / 0.593 / 0.584 | -1% | 0.649 / 0.649 / 0.639 | -2% |
| Lubbock city | 0.909 / 0.909 / 0.899 | -1% | 0.597 / 0.597 / 0.571 | -4% | 0.751 / 0.751 / 0.715 | -5% |
| Virginia Beach city | 0.929 / 0.933 / 0.914 | -2% | 0.618 / 0.667 / 0.718 | +8% | 0.622 / 0.631 / 0.441 | -30% |
| Bristol city | 0.842 / 0.853 / 0.857 | +0% | 0.405 / 0.408 / 0.451 | +11% | 0.292 / 0.327 / 0.376 | +15% |
| Loudoun County | 0.914 / 0.914 / 0.911 | -0% | 0.604 / 0.604 / 0.589 | -2% | 0.592 / 0.592 / 0.583 | -2% |
| Richmond city | 0.929 / 0.929 / 0.923 | -1% | 0.618 / 0.618 / 0.625 | +1% | 0.622 / 0.622 / 0.637 | +2% |
| Roanoke city | 0.892 / 0.892 / 0.871 | -2% | 0.553 / 0.553 / 0.478 | -14% | 0.560 / 0.560 / 0.435 | -22% |
| Lorain city | 0.900 / 0.893 / 0.899 | +1% | 0.565 / 0.567 / 0.714 | +26% | 0.508 / 0.471 / 0.382 | -19% |
| Toledo city | 0.900 / 0.904 / 0.905 | +0% | 0.565 / 0.583 / 0.589 | +1% | 0.508 / 0.552 / 0.519 | -6% |
| Cincinnati city | 0.905 / 0.905 / 0.902 | -0% | 0.537 / 0.537 / 0.579 | +8% | 0.487 / 0.487 / 0.503 | +3% |
| Cleveland city | 0.893 / 0.893 / 0.890 | -0% | 0.567 / 0.567 / 0.587 | +4% | 0.471 / 0.471 / 0.395 | -16% |
| Columbus city | 0.905 / 0.905 / 0.892 | -1% | 0.562 / 0.562 / 0.564 | +0% | 0.478 / 0.478 / 0.461 | -4% |
| Port Huron city | 0.894 / 0.915 / 0.889 | -3% | 0.583 / 0.641 / 0.606 | -6% | 0.478 / 0.582 / 0.447 | -23% |
| Ironwood city | 0.870 / 0.860 / 0.876 | +2% | 0.547 / 0.518 / 0.530 | +2% | 0.397 / 0.387 / 0.449 | +16% |
| Gaines charter township | 0.887 / 0.902 / 0.899 | -0% | 0.574 / 0.603 / 0.600 | -0% | 0.415 / 0.487 / 0.448 | -8% |

| Place | Design dry-bulb, station (C) | ERA5 (C) |
|---|---|---|
| Austin city | 37.8 | 38.1 |
| San Antonio city | 37.8 | 37.8 |
| Round Rock city | 38.9 | 38.0 |
| Dallas city | 38.9 | 38.4 |
| El Paso city | 38.9 | 38.4 |
| Amarillo city | 37.2 | 36.8 |
| Virginia Beach city | 33.9 | 30.9 |
| Bristol city | 31.1 | 31.1 |
| Lorain city | 32.2 | 29.6 |
| Toledo city | 32.8 | 32.2 |
| Port Huron city | 32.2 | 30.2 |
| Ironwood city | 29.0 | 30.8 |
| Gaines charter township | 31.7 | 31.4 |


## What it shows

**Towers don't care.** ERA5 is within 1% of the nearest station on the average day at all 21 places, and within 3% on the
peak day, as the stations were with each other on Oct 29.

**Inland, ERA5 agrees with the nearby station.** On the 16 cells that are at least 90% land, ERA5's hybrid average is within
9% of the nearest qualifying station at 14, and its assist average within 9% at 13 (in Texas every comparison is within 9%). It fixes the
far-station cases the Oct 29 check found. Austin's assist peak day was published 20% below San Antonio's station; ERA5 at
Austin is 3% below it. Amarillo's hybrid average was published 22% above Amarillo's own airport; ERA5 is 5% above it. El
Paso's hybrid peak was 13% below; ERA5 is 7% below. Of the 13 places with a nearer station than the published one, ERA5 is
closer to that station than the published number is in 9 for the hybrid average and in 9 for the hybrid peak day.

**Two inland places differ.**
- **Roanoke:** ERA5 is 14-22% below for hybrid and assist. Roanoke's airport sits in the valley, and its cell averages the
  valley with the ridges around it.
- **Ironwood:** ERA5 is 41% (hybrid) and 84% (assist) above Houghton County's station. Houghton is 150 km away on the
  Keweenaw Peninsula, beside Lake Superior, so ERA5 is the likelier of the two here. The amounts are small (0.005-0.009 MGD per
  100 MW).

**Cells that are part lake or sea run low for hybrid and assist on average.** These are Lorain (land share 0.40), Virginia
Beach (0.51), Cleveland (0.65), Port Huron (0.75) and Toledo (0.78):
- **Hybrid average:** 6-39% below the nearest station.
- **Assist average:** 11-52% below.
- **Design dry-bulb:** 2-3 C lower at Lorain, Virginia Beach and Port Huron.

Their air is moderated by the water, and an airport on the shore isn't. Two of them go the other way on the peak day:
Lorain's hybrid peak is 26% above the station and Virginia Beach's 8%. This is consistent with the lower design dry-bulb: a
hybrid is fully evaporative at the design dry-bulb plus an offset (`physics.hybrid_full`), so a lower one makes it run wetter on
its hottest days. Of the five, only Lorain is among the 189 places (MI 116, OH 35, VA 23, TX 15) whose nearest cell is
mostly water, which the land rule of Nov 3 moves (below); the other four are on cells half to nine-tenths land. Both kinds
are the case quantile mapping is for (decided Nov 4 for model 1.8: [design 0005](../design/0005-era5-quantile-mapping.md)).

**Against what is published today**, ERA5 moves the hybrid average by -21% to +60% (median -5%) and the assist average by -50%
to +83% (median -8%), across these 21 places. Towers move by 2% or less. The largest moves are where today's point is far
away (Bristol, Ironwood) or where the cell is part water (Port Huron, Lorain, Virginia Beach).

**The weather source still matters, less than on Oct 29.** On Oct 29 (model 1.2), Grand Rapids airport gave Gaines Township a
hybrid average 23% above the ERA5 point 11 km away. Here ERA5 at Gaines's own cell is 3% below the airport. The model
changed between the two checks (1.2 to 1.7), so the two numbers aren't directly comparable.

## The land rule (added Nov 3, 2026)

On Nov 3 Andrew decided that a place whose nearest cell is mostly water (land-sea mask under 0.5) takes the nearest cell,
by great-circle distance, that is at least half land ([design 0004](../design/0004-era5-weather.md), decision 3). The rule
moves 189 places in the four states, and every place's cell is listed in
[era5-check/cell_assignment.csv](era5-check/cell_assignment.csv) (from `land_rule.py`).

**Virginia's Eastern Shore moves farthest.** Its 19 places sit on mostly-sea cells. Five go across the Chesapeake to the
western shore: Cape Charles, Cheriton, Eastville and Northampton County to 37.25, -76.50 by Yorktown (43-52 km, land 0.51)
and Nassawadox to 37.50, -76.50 (57 km, land 0.68). The rest go north up the peninsula: Exmore, Belle Haven, Painter,
Wachapreague, Keller, Melfa, Onley, Onancock, Accomac, Parksley, Accomack County and Tangier to 38.00, -75.75 at the
Maryland line (25-53 km, land 0.67), and Bloxom and Chincoteague to 38.00, -75.50 (14-22 km, land 0.58). Hampton Roads'
four moved places (Norfolk, Hampton, Poquoson, Mathews County) go 19-22 km and stay on their side of the bay. Elsewhere the
farthest moves are Michigan's island townships (Isle Royale to the Ontario shore, 55-60 km; Beaver Island, North Manitou,
Drummond Island and the Garden Peninsula's tip, 37-44 km); 165 of the 189 move 30 km or less.

**Of this check's five part-water places, only Lorain moves.** Lorain's nearest cell is 0.40 land; Virginia Beach (0.51),
Cleveland (0.65), Port Huron (0.75) and Toledo (0.78) are at least half land and keep their cells, so their numbers don't
change. The five were rerun the same way as above (`land_rule_check.py`), on the rule's cell and, as a sensitivity only, on
the nearest cell at least 90% land, which is not the rule.

| Place | Station (km) | Nearest cell (km, land) | Land rule (km, land) | At least 90% land (sensitivity) (km, land) |
|---|---|---|---|---|
| Lorain city, OH | Cleveland-Hopkins Intl (28) | 41.50, -82.25 (9, 0.40) | 41.50, -82.00 (16, 0.59) | 41.25, -82.00 (26, 0.93) |
| Virginia Beach city, VA | Oceana Nas (4) | 36.75, -76.00 (4, 0.51) | 36.75, -76.00 (4, 0.51) | 36.50, -76.50 (52, 0.99) |
| Cleveland city, OH | Cleveland-Hopkins Intl (16) | 41.50, -81.75 (6, 0.65) | 41.50, -81.75 (6, 0.65) | 41.25, -81.75 (26, 0.94) |
| Port Huron city, MI | Detroit City (80) | 43.00, -82.50 (5, 0.75) | 43.00, -82.50 (5, 0.75) | 43.00, -82.75 (26, 0.98) |
| Toledo city, OH | Toledo Express (20) | 41.75, -83.50 (12, 0.78) | 41.75, -83.50 (12, 0.78) | 41.75, -83.75 (17, 0.93) |

#### Against the nearest station, average day (p50, per 100 MW): nearest cell / land rule / at least 90% land

| Place | Towers | Hybrid | Assist |
|---|---|---|---|
| Lorain city | -0% / -0% / -0% | -10% / -8% / -2% | -39% / -35% / -12% |
| Virginia Beach city | -0% / -0% / +0% | -10% / -10% / +1% | -44% / -44% / -0% |
| Cleveland city | -0% / -0% / -0% | -11% / -11% / -6% | -27% / -27% / -13% |
| Port Huron city | -1% / -1% / -1% | -39% / -39% / -31% | -52% / -52% / -34% |
| Toledo city | +0% / +0% / -0% | -6% / -6% / -3% | -11% / -11% / -5% |

#### Against the nearest station, 1-in-10 peak day (p50, per 100 MW): nearest cell / land rule / at least 90% land

| Place | Towers | Hybrid | Assist |
|---|---|---|---|
| Lorain city | +1% / +0% / -0% | +26% / +18% / +1% | -19% / -22% / -7% |
| Virginia Beach city | -2% / -2% / -1% | +8% / +8% / -12% | -30% / -30% / -15% |
| Cleveland city | -0% / -0% / -1% | +4% / +4% / -3% | -16% / -16% / -8% |
| Port Huron city | -3% / -3% / -2% | -6% / -6% / -11% | -23% / -23% / -16% |
| Toledo city | +0% / +0% / -0% | +1% / +1% / -2% | -6% / -6% / -7% |

| Place | Design dry-bulb, station (C) | Nearest cell | Land rule | At least 90% land |
|---|---|---|---|---|
| Lorain city | 32.2 | 29.6 | 29.9 | 31.4 |
| Virginia Beach city | 33.9 | 30.9 | 30.9 | 33.9 |
| Cleveland city | not run | 30.7 | 30.7 | 31.5 |
| Port Huron city | 32.2 | 30.2 | 30.2 | 31.4 |
| Toledo city | 32.8 | 32.2 | 32.2 | 32.5 |

- **Lorain** moves 16 km east to a cell 0.59 land. The gap to Cleveland-Hopkins narrows a little: hybrid average
  -10% to -8%, assist -39% to -35%, hybrid peak day +26% to +18%, design dry-bulb 0.3 C warmer. The new cell is still
  41% lake.
- **Virginia Beach, Cleveland, Port Huron and Toledo** don't change under the rule.
- **The sensitivity** shows where the bias sits. On the nearest cell at least 90% land (17-52 km away), Lorain's and
  Virginia Beach's hybrid averages come within 2% of the station and Virginia Beach's design dry-bulb matches it; Cleveland
  and Toledo come within 6% for hybrid. Port Huron stays 31-34% low, but its station is Detroit City, 80 km south, so that
  comparison says as much about the station as the cell.

The rule removes the cells that are mostly water, and the larger gap is on shore cells that are half to nine-tenths land:
777 places stay on them (Michigan 462, Ohio 172, Virginia 56, Texas 87). Quantile mapping, or a stricter threshold, is what
would address those; neither is decided.

## Limits

- 21 places, chosen on Oct 29 where the station was expected to matter. They are not a statewide distribution; the full run
  gives one.
- The nearest qualifying station is a reference, not the truth: airports stand for a point, often on a shore or in a valley.
- ERA5 here is Open-Meteo's copy, in 0.05 C steps; the build's source (CDS) gives the same field unrounded. The steps are below
  the screens' and the stations' own resolution (0.1 C) and were not tested for effect.
- The p50 of one 400-draw Latin hypercube with a fixed seed; differences between weather records are single comparisons.
- Times are local standard time from longitude, for stations and ERA5 alike.

## Data

- Hersbach, H., et al. (2023). ERA5 hourly data on single levels from 1940 to present. Copernicus Climate Change Service
  (C3S) Climate Data Store. doi:10.24381/cds.adbb2d47. Read from Open-Meteo's open-data copy, s3://openmeteo/data/copernicus_era5
  (CC-BY 4.0). Generated using Copernicus Climate Change Service information 2026. Neither the European Commission nor ECMWF
  is responsible for any use that may be made of the Copernicus information or data it contains.
- Hersbach, H., et al. (2020). The ERA5 global reanalysis. Quarterly Journal of the Royal Meteorological Society 146(730):
  1999-2049.
- ERA5 land-sea mask, from Google's ARCO-ERA5 copy (gs://gcp-public-data-arco-era5).
- NOAA NCEI Integrated Surface Database, ISD-Lite, 1995-2024 (as in the Oct 29 check).
- Water Ledger snapshots for Michigan, Ohio, Virginia and Texas dated 2026-11-02.2 (model 1.7).
