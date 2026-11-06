# ERA5 check: WI

**FAIL** (2026-11-05; model 1.8; design 0005's leave-one-station-out check; 29 stations).

| Criterion | Test | Limit | Value | Pass | Limit set from |
|---|---|---|---|---|---|
| W1 | land stations held out, at least | 5 | 22 | yes | too few to judge below this |
| W2 | land cells: median |error| in the 0.4% design dry-bulb, C, at most | 0.75 | 0.70 | yes | four states 0.30-0.68 (Virginia); +0.07 |
| W3 | land cells: |mean error| in the design dry-bulb, C, at most | 0.50 | 0.60 | **no** | four states 0.07-0.33 (Texas); +0.17 |
| W4 | land cells: median |error| in the 0.4% wet bulb, C, at most | 0.40 | 0.19 | yes | four states 0.10-0.25 (Virginia); +0.15 |
| W5 | corrected shore cells (3 or more): median |error| in the design dry-bulb, C, at most | 0.50 | 0.41 | yes | four states 0.19-0.32 (Michigan); +0.18 |
| W6 | corrected shore cells (3 or more): median |error| no worse than uncorrected | - | 0.41 vs 1.80 | yes | the reason to correct |
| P1 | places sampled, at least | 5 | 12 | yes | too few to judge below this |
| P2 | places: median |difference| in the hybrid average day, %, at most | 8.00 | 5.93 | yes | four states 1.9-4.6 (Virginia); +3.4 |
| P3 | places: |mean difference| in the hybrid average day, %, at most | 6.00 | 6.82 | **no** | four states 0.6-4.9 (Virginia); +1.1 |
| P4 | places: median |difference| in the hybrid peak day, %, at most | 6.00 | 3.68 | yes | four states 0.5-3.2 (Virginia); +2.8 |
| P5 | places: median |difference| in towers' average day, %, at most | 2.00 | 0.10 | yes | four states 0.03-0.22; +1.8 |

## Weather at the held-out stations

Median absolute error (mean error), C, against the station on its own hours.

| Stations | Way | Design dry-bulb | 0.4% wet bulb | Summer afternoon T | Mean dew point |
|---|---|---|---|---|---|
| land cells (22) | uncorrected | 0.70 (-0.60) | 0.19 (-0.21) | 0.38 (-0.39) | 0.21 (+0.10) |
| shore cells, corrected (6) | uncorrected | 1.80 (-1.76) | 0.28 (-0.29) | 0.92 (-0.90) | 0.42 (+0.47) |
| shore cells, corrected (6) | decided | 0.41 (-0.36) | 0.35 (+0.37) | 0.83 (-0.08) | 0.13 (-0.05) |
| shore cells, no shore station (1) | uncorrected | 1.00 (-1.00) | 0.46 (+0.46) | 0.10 (-0.10) | 0.88 (+0.88) |

| Station | Source | Cell land | Design dry-bulb error (C) | Corrected from |
|---|---|---|---|---|
| Whittman Regional Airport, WI | isd-linked | 0.53 | +0.41 | Fond Du Lac County Airport 26 km |
| Waukegan Regional Airport, IL | isd-linked | 0.73 | +0.12 | Kenosha Regional Airport 12 km, General Mitchell International Ap 51 km, Chicago Midway Intl Arpt 82 km |
| Kenosha Regional Airport, WI | isd-linked | 0.73 | -0.41 | Waukegan Regional Airport 14 km, General Mitchell International Ap 51 km, Chicago Midway Intl Arpt 82 km |
| General Mitchell International Ap, WI | isd | 0.75 | -0.25 | Kenosha Regional Airport 45 km, Waukegan Regional Airport 65 km, Fond Du Lac County Airport 94 km |
| Duluth International Airport, MN | isd | 0.81 | -1.00 | no shore station within 100 km |
| Chicago Midway Intl Arpt, IL | isd | 0.82 | -1.09 | Waukegan Regional Airport 76 km, Kenosha Regional Airport 95 km |
| Fond Du Lac County Airport, WI | isd-linked | 0.89 | -0.92 | Whittman Regional Airport 27 km |
| Rhinelander-Oneida Co Arpt, WI | isd-linked | 0.90 | -1.30 | cell at least 90% land |
| Sawyer County Airport, WI | isd-linked | 0.92 | -0.85 | cell at least 90% land |
| St Paul Dwtwn Holman Fd Ap, MN | isd-linked | 0.93 | -0.95 | cell at least 90% land |
| Dubuque Regional Airport, IA | isd | 0.93 | +0.60 | cell at least 90% land |
| Minneapolis-St Paul International Ap, MN | isd | 0.94 | -0.95 | cell at least 90% land |
| Crystal Airport, MN | isd-linked | 0.94 | -0.85 | cell at least 90% land |
| Austin Straubel International Ap, WI | isd | 0.95 | +0.60 | cell at least 90% land |
| Flying Cloud Airport, MN | isd-linked | 0.96 | -0.85 | cell at least 90% land |
| Dane Co Regional-Truax Field Airport, WI | isd | 0.96 | -0.25 | cell at least 90% land |
| Alexander Fd S Wood Co Apt, WI | isd-linked | 0.96 | -0.95 | cell at least 90% land |
| La Crosse Municipal Airport, WI | isd | 0.96 | -1.95 | cell at least 90% land |
| Chisholm-Hibbing Airport, MN | isd | 0.97 | -0.00 | cell at least 90% land |
| Chicago O'Hare International Airport, IL | isd | 0.98 | -0.45 | cell at least 90% land |
| Ford Airport, MI | isd-linked | 0.98 | -0.30 | cell at least 90% land |
| Wausau Downtown Airport, WI | isd | 0.98 | -1.30 | cell at least 90% land |
| Chippewa Valley Rgnl Arpt, WI | isd | 0.99 | -0.85 | cell at least 90% land |
| Dupage Airport, IL | isd-linked | 0.99 | -0.10 | cell at least 90% land |
| Tri-County Regional Arpt, WI | isd-linked | 0.99 | -0.65 | cell at least 90% land |
| Greater Rockford Airport, IL | isd | 1.00 | -0.75 | cell at least 90% land |
| Aurora Municipal Airport, IL | isd-linked | 1.00 | -0.65 | cell at least 90% land |
| Marshfield Municipal Arpt, WI | isd-linked | 1.00 | -0.25 | cell at least 90% land |
| Rochester International Airport, MN | isd | 1.00 | -0.10 | cell at least 90% land |

## Places through the cooling model

The place's cell against the station's own record, p50 per 100 MW, % difference.

| Place | Station (km) | Cell land | towers avg | towers peak | hybrid avg | hybrid peak | assist avg | assist peak |
|---|---|---|---|---|---|---|---|---|
| St. Francis city | General Mitchell International Ap (3) | 0.75 | -0 | +2 | +6 | +3 | -3 | -1 |
| Oshkosh city | Whittman Regional Airport (4) | 0.53 | +0 | +1 | +6 | +6 | +10 | +10 |
| Somers town | Kenosha Regional Airport (4) | 0.73 | -0 | +2 | -18 | +10 | -22 | +5 |
| Fond du Lac County | Fond Du Lac County Airport (2) | 0.89 | -1 | -0 | -15 | +3 | -22 | -6 |
| Burke town | Dane Co Regional-Truax Field Airport (3) | 0.96 | -0 | -1 | -4 | -4 | -5 | -2 |
| Lone Rock village | Tri-County Regional Arpt (3) | 0.99 | +0 | +1 | -5 | +8 | -7 | +4 |
| Campbell town | La Crosse Municipal Airport (3) | 0.96 | -1 | -2 | -18 | -6 | -28 | -18 |
| Eau Claire city | Chippewa Valley Rgnl Arpt (5) | 0.99 | +0 | -0 | -6 | +4 | -11 | -2 |
| Hobart village | Austin Straubel International Ap (2) | 0.95 | +0 | +0 | +3 | +2 | +15 | +14 |
| Port Edwards village | Alexander Fd S Wood Co Apt (1) | 0.96 | +0 | +1 | -3 | +14 | -9 | +10 |
| Schofield city | Wausau Downtown Airport (2) | 0.98 | -0 | -2 | -18 | +0 | -30 | -10 |
| Hayward city | Sawyer County Airport (4) | 0.92 | +0 | -1 | -9 | -3 | -18 | -7 |

A fail is a method question for Andrew; the command changes nothing. Criteria: `waterledger.national.era5_check.CRITERIA`.
