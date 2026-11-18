# ERA5 check: WI

**PASS** (2026-11-16; model 1.16; design 0005's leave-one-station-out check; 29 stations).

| Criterion | Test | Limit | Value | Pass | Limit set from |
|---|---|---|---|---|---|
| W1 | land stations held out, at least | 5 | 22 | yes | too few to judge below this |
| W2 | land cells: median |error| in the 0.4% design dry-bulb, C, at most | 0.75 | 0.40 | yes | four states 0.30-0.68 (Virginia); +0.07 |
| W3 | land cells: |mean error| in the design dry-bulb, C, at most | 0.50 | 0.18 | yes | four states 0.07-0.33 (Texas); +0.17 |
| W4 | land cells: median |error| in the 0.4% wet bulb, C, at most | 0.40 | 0.21 | yes | four states 0.10-0.25 (Virginia); +0.15 |
| W5 | corrected shore cells (3 or more): median |error| in the design dry-bulb, C, at most | 0.50 | 0.41 | yes | four states 0.19-0.32 (Michigan); +0.18 |
| W6 | corrected shore cells (3 or more): median |error| no worse than uncorrected | - | 0.41 vs 1.80 | yes | the reason to correct |
| W7 | corrected cells: |mean error| in the 1-in-10-year peak day's mean wet bulb, C, at most | 0.50 | 0.02 | yes | model 1.10 [A]: qm-2's Michigan peak days ran 0.72 C humid, mapping the dew point brought Michigan and Ohio to 0.23 (methods log, Nov 8, 2026) |
| P1 | places sampled, at least | 5 | 12 | yes | too few to judge below this |
| P2 | places: median |difference| in the hybrid average day, % of towers' average day, at most | 1.00 | 0.24 | yes | four states at 1.16 0.10-0.53 (Texas); +0.47 |
| P3 | places: |mean difference| in the hybrid average day, % of towers' average day, at most | 0.75 | 0.12 | yes | four states at 1.16 0.04-0.29 (Texas); +0.46 |
| P4 | places: median |difference| in the hybrid peak day, % of towers' peak day, at most | 6.00 | 4.72 | yes | four states at 1.16 1.5-4.0 (Ohio); +2.0 |
| P5 | places: median |difference| in towers' average day, %, at most | 2.00 | 0.25 | yes | four states 0.03-0.22; +1.8 |
| P6 | places: median |difference| in the pads average day, % of towers' average day, at most | 1.00 | 0.23 | yes | four states at 1.16 0.17-0.54 (Texas); +0.46 |
| P7 | places: median |difference| in the pads peak day, % of towers' peak day, at most | 6.00 | 1.66 | yes | four states at 1.16 1.3-3.8 (Texas); +2.2 |

## Weather at the held-out stations

Median absolute error (mean error), C, against the station on its own hours.

| Stations | Way | Design dry-bulb | 0.4% wet bulb | Summer afternoon T | Mean dew point |
|---|---|---|---|---|---|
| land cells, corrected (17) | uncorrected | 0.85 (-0.73) | 0.21 (-0.23) | 0.46 (-0.46) | 0.19 (+0.08) |
| land cells, corrected (17) | decided | 0.42 (-0.19) | 0.22 (-0.04) | 0.28 (-0.04) | 0.18 (+0.05) |
| land cells, no station (5) | uncorrected | 0.30 (-0.13) | 0.15 (-0.15) | 0.18 (-0.13) | 0.41 (+0.16) |
| shore cells, corrected (6) | uncorrected | 1.80 (-1.76) | 0.28 (-0.29) | 0.92 (-0.90) | 0.42 (+0.47) |
| shore cells, corrected (6) | decided | 0.41 (-0.36) | 0.22 (-0.12) | 0.83 (-0.08) | 0.07 (+0.02) |
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
| Rhinelander-Oneida Co Arpt, WI | isd-linked | 0.90 | +0.19 | Wausau Downtown Airport 92 km |
| Sawyer County Airport, WI | isd-linked | 0.92 | -0.85 | no land station within 100 km |
| St Paul Dwtwn Holman Fd Ap, MN | isd-linked | 0.93 | -0.17 | Minneapolis-St Paul International Ap 22 km, Crystal Airport 28 km, Flying Cloud Airport 42 km |
| Dubuque Regional Airport, IA | isd | 0.93 | +0.66 | Tri-County Regional Arpt 91 km |
| Minneapolis-St Paul International Ap, MN | isd | 0.94 | -0.45 | Crystal Airport 10 km, St Paul Dwtwn Holman Fd Ap 17 km, Flying Cloud Airport 26 km |
| Crystal Airport, MN | isd-linked | 0.94 | -0.25 | Minneapolis-St Paul International Ap 13 km, St Paul Dwtwn Holman Fd Ap 17 km, Flying Cloud Airport 26 km |
| Austin Straubel International Ap, WI | isd | 0.95 | +0.60 | no land station within 100 km |
| Flying Cloud Airport, MN | isd-linked | 0.96 | -0.26 | Minneapolis-St Paul International Ap 26 km, Crystal Airport 37 km, St Paul Dwtwn Holman Fd Ap 40 km |
| Dane Co Regional-Truax Field Airport, WI | isd | 0.96 | +0.07 | Tri-County Regional Arpt 76 km |
| Alexander Fd S Wood Co Apt, WI | isd-linked | 0.96 | -0.87 | Marshfield Municipal Arpt 55 km, Wausau Downtown Airport 76 km |
| La Crosse Municipal Airport, WI | isd | 0.96 | -1.28 | Chippewa Valley Rgnl Arpt 98 km, Rochester International Airport 100 km |
| Chisholm-Hibbing Airport, MN | isd | 0.97 | -0.00 | no land station within 100 km |
| Chicago O'Hare International Airport, IL | isd | 0.98 | -0.42 | Dupage Airport 24 km, Aurora Municipal Airport 47 km, Greater Rockford Airport 93 km |
| Ford Airport, MI | isd-linked | 0.98 | -0.30 | no land station within 100 km |
| Wausau Downtown Airport, WI | isd | 0.98 | -0.42 | Marshfield Municipal Arpt 68 km, Rhinelander-Oneida Co Arpt 70 km, Alexander Fd S Wood Co Apt 76 km |
| Chippewa Valley Rgnl Arpt, WI | isd | 0.99 | +0.39 | La Crosse Municipal Airport 99 km |
| Dupage Airport, IL | isd-linked | 0.99 | +0.36 | Chicago O'Hare International Airport 27 km, Aurora Municipal Airport 32 km, Greater Rockford Airport 73 km |
| Tri-County Regional Arpt, WI | isd-linked | 0.99 | -0.63 | Dane Co Regional-Truax Field Airport 74 km |
| Greater Rockford Airport, IL | isd | 1.00 | -0.49 | Aurora Municipal Airport 68 km, Dupage Airport 73 km, Chicago O'Hare International Airport 94 km |
| Aurora Municipal Airport, IL | isd-linked | 1.00 | -0.29 | Dupage Airport 26 km, Chicago O'Hare International Airport 52 km, Greater Rockford Airport 70 km |
| Marshfield Municipal Arpt, WI | isd-linked | 1.00 | +0.60 | Wausau Downtown Airport 53 km, Alexander Fd S Wood Co Apt 54 km, Chippewa Valley Rgnl Arpt 98 km |
| Rochester International Airport, MN | isd | 1.00 | -0.10 | no land station within 100 km |

## Places through the cooling model

The place's cell against the station's own record, p50 per 100 MW: % difference in each design's own water (towers are judged by this one), then hybrid and pads as % of towers' water at the place (judged from model 1.16).

| Place | Station (km) | Cell land | towers avg | towers peak | hybrid avg | hybrid peak | assist avg | assist peak |
|---|---|---|---|---|---|---|---|---|
| St. Francis city | General Mitchell International Ap (3) | 0.75 | -0 | +1 | +6 | +8 | +2 | +3 |
| Oshkosh city | Whittman Regional Airport (4) | 0.53 | +0 | +1 | +15 | +11 | +19 | +8 |
| Somers town | Kenosha Regional Airport (4) | 0.73 | -0 | +1 | -24 | +9 | -30 | +8 |
| Fond du Lac County | Fond Du Lac County Airport (2) | 0.89 | -1 | +0 | -28 | +8 | -35 | -3 |
| Burke town | Dane Co Regional-Truax Field Airport (3) | 0.96 | -0 | -1 | +2 | -5 | +1 | -4 |
| Lone Rock village | Tri-County Regional Arpt (3) | 0.99 | -0 | +1 | -20 | +14 | -24 | +4 |
| Campbell town | La Crosse Municipal Airport (3) | 0.96 | -1 | -2 | -32 | -9 | -41 | -25 |
| Eau Claire city | Chippewa Valley Rgnl Arpt (5) | 0.99 | +1 | +2 | +19 | +11 | +22 | +6 |
| Hobart village | Austin Straubel International Ap (2) | 0.95 | -0 | +0 | +16 | +9 | +33 | +21 |
| Port Edwards village | Alexander Fd S Wood Co Apt (1) | 0.96 | -0 | +0 | -22 | +13 | -26 | +9 |
| Schofield city | Wausau Downtown Airport (2) | 0.98 | -0 | -0 | -12 | +4 | -15 | +1 |
| Hayward city | Sawyer County Airport (4) | 0.92 | +0 | -1 | -27 | +0 | -29 | -4 |

| Place | hybrid avg, % of towers | hybrid peak, % of towers | assist avg, % of towers | assist peak, % of towers |
|---|---|---|---|---|
| St. Francis city | +0.07 | +4.47 | +0.01 | +0.97 |
| Oshkosh city | +0.15 | +4.96 | +0.12 | +2.06 |
| Somers town | -0.35 | +5.13 | -0.33 | +2.64 |
| Fond du Lac County | -0.34 | +3.81 | -0.30 | -0.78 |
| Burke town | +0.02 | -2.79 | +0.01 | -1.12 |
| Lone Rock village | -0.31 | +7.01 | -0.28 | +1.36 |
| Campbell town | -0.56 | -5.19 | -0.67 | -10.14 |
| Eau Claire city | +0.25 | +5.57 | +0.23 | +1.97 |
| Hobart village | +0.16 | +4.44 | +0.22 | +5.89 |
| Port Edwards village | -0.27 | +5.97 | -0.24 | +2.51 |
| Schofield city | -0.10 | +1.64 | -0.09 | +0.32 |
| Hayward city | -0.22 | +0.21 | -0.17 | -1.19 |

A fail is a method question for Andrew; the command changes nothing. Criteria: `waterledger.national.era5_check.CRITERIA`.
