# ERA5 check: IL

**PASS** (2026-11-16; model 1.16; design 0005's leave-one-station-out check; 34 stations).

| Criterion | Test | Limit | Value | Pass | Limit set from |
|---|---|---|---|---|---|
| W1 | land stations held out, at least | 5 | 30 | yes | too few to judge below this |
| W2 | land cells: median |error| in the 0.4% design dry-bulb, C, at most | 0.75 | 0.35 | yes | four states 0.30-0.68 (Virginia); +0.07 |
| W3 | land cells: |mean error| in the design dry-bulb, C, at most | 0.50 | 0.09 | yes | four states 0.07-0.33 (Texas); +0.17 |
| W4 | land cells: median |error| in the 0.4% wet bulb, C, at most | 0.40 | 0.19 | yes | four states 0.10-0.25 (Virginia); +0.15 |
| W5 | corrected shore cells (3 or more): median |error| in the design dry-bulb, C, at most | 0.50 | 0.30 | yes | four states 0.19-0.32 (Michigan); +0.18 |
| W6 | corrected shore cells (3 or more): median |error| no worse than uncorrected | - | 0.30 vs 2.03 | yes | the reason to correct |
| W7 | corrected cells: |mean error| in the 1-in-10-year peak day's mean wet bulb, C, at most | 0.50 | 0.13 | yes | model 1.10 [A]: qm-2's Michigan peak days ran 0.72 C humid, mapping the dew point brought Michigan and Ohio to 0.23 (methods log, Nov 8, 2026) |
| P1 | places sampled, at least | 5 | 12 | yes | too few to judge below this |
| P2 | places: median |difference| in the hybrid average day, % of towers' average day, at most | 1.00 | 0.15 | yes | four states at 1.16 0.10-0.53 (Texas); +0.47 |
| P3 | places: |mean difference| in the hybrid average day, % of towers' average day, at most | 0.75 | 0.08 | yes | four states at 1.16 0.04-0.29 (Texas); +0.46 |
| P4 | places: median |difference| in the hybrid peak day, % of towers' peak day, at most | 6.00 | 4.48 | yes | four states at 1.16 1.5-4.0 (Ohio); +2.0 |
| P5 | places: median |difference| in towers' average day, %, at most | 2.00 | 0.17 | yes | four states 0.03-0.22; +1.8 |
| P6 | places: median |difference| in the pads average day, % of towers' average day, at most | 1.00 | 0.25 | yes | four states at 1.16 0.17-0.54 (Texas); +0.46 |
| P7 | places: median |difference| in the pads peak day, % of towers' peak day, at most | 6.00 | 4.21 | yes | four states at 1.16 1.3-3.8 (Texas); +2.2 |

## Weather at the held-out stations

Median absolute error (mean error), C, against the station on its own hours.

| Stations | Way | Design dry-bulb | 0.4% wet bulb | Summer afternoon T | Mean dew point |
|---|---|---|---|---|---|
| land cells, corrected (27) | uncorrected | 0.45 (-0.24) | 0.34 (-0.33) | 0.24 (-0.17) | 0.19 (-0.12) |
| land cells, corrected (27) | decided | 0.35 (-0.07) | 0.18 (-0.15) | 0.23 (+0.01) | 0.22 (-0.02) |
| land cells, no station (3) | uncorrected | 0.35 (-0.30) | 0.29 (-0.25) | 0.35 (-0.07) | 0.12 (-0.07) |
| shore cells, corrected (4) | uncorrected | 2.03 (-1.95) | 0.28 (-0.30) | 0.87 (-0.90) | 0.42 (+0.44) |
| shore cells, corrected (4) | decided | 0.30 (-0.39) | 0.31 (-0.10) | 0.96 (-0.12) | 0.19 (+0.03) |

| Station | Source | Cell land | Design dry-bulb error (C) | Corrected from |
|---|---|---|---|---|
| Waukegan Regional Airport, IL | isd-linked | 0.73 | +0.12 | Kenosha Regional Airport 12 km, General Mitchell International Ap 51 km, Chicago Midway Intl Arpt 82 km |
| Kenosha Regional Airport, WI | isd-linked | 0.73 | -0.41 | Waukegan Regional Airport 14 km, General Mitchell International Ap 51 km, Chicago Midway Intl Arpt 82 km |
| General Mitchell International Ap, WI | isd | 0.75 | -0.18 | Kenosha Regional Airport 45 km, Waukegan Regional Airport 65 km |
| Chicago Midway Intl Arpt, IL | isd | 0.82 | -1.09 | Waukegan Regional Airport 76 km, Kenosha Regional Airport 95 km |
| Dubuque Regional Airport, IA | isd | 0.93 | +0.66 | Tri-County Regional Arpt 91 km |
| Spirit Of St Louis Airport, MO | isd | 0.96 | +0.38 | Lambert-St Louis International Ap 33 km, St Louis Downtown Airport 56 km, Scott Air Force Base/Midamerica Airport 81 km |
| Dane Co Regional-Truax Field Airport, WI | isd | 0.96 | +0.07 | Tri-County Regional Arpt 76 km |
| Greater Peoria Regional Airport, IL | isd | 0.96 | -0.35 | no land station within 100 km |
| Se Iowa Regional Airport, IA | isd-linked | 0.97 | +0.36 | Quad City International Airport 87 km, Quincy Rgnl-Bldwn Fld Arpt 92 km |
| Lambert-St Louis International Ap, MO | isd | 0.97 | -0.78 | St Louis Downtown Airport 22 km, Spirit Of St Louis Airport 37 km, Scott Air Force Base/Midamerica Airport 41 km |
| Quad City International Airport, IL | isd | 0.97 | -0.03 | Iowa City Municipal Arpt 88 km, Se Iowa Regional Airport 96 km |
| Chicago O'Hare International Airport, IL | isd | 0.98 | -0.42 | Dupage Airport 24 km, Aurora Municipal Airport 47 km, Greater Rockford Airport 93 km |
| Barkley Regional Airport, KY | isd | 0.98 | -0.16 | Cape Girardeau Rgnl Arpt 78 km, Southern Illinois Airport 97 km |
| Cape Girardeau Rgnl Arpt, MO | isd-linked | 0.98 | -0.20 | Southern Illinois Airport 63 km, Barkley Regional Airport 68 km |
| Monroe County Airport, IN | isd-linked | 0.98 | +0.12 | Ter Hute Intl-Hulman Fd Ap 74 km |
| Quincy Rgnl-Bldwn Fld Arpt, IL | isd-linked | 0.98 | -0.52 | Se Iowa Regional Airport 87 km |
| St Louis Downtown Airport, IL | isd-linked | 0.98 | +0.26 | Lambert-St Louis International Ap 30 km, Scott Air Force Base/Midamerica Airport 35 km, Spirit Of St Louis Airport 39 km |
| Iowa City Municipal Arpt, IA | isd-linked | 0.98 | -0.91 | Eastern Iowa Regional Airport 24 km, Quad City International Airport 88 km, Dubuque Regional Airport 97 km |
| Southern Illinois Airport, IL | isd-linked | 0.98 | +0.18 | Cape Girardeau Rgnl Arpt 65 km, Barkley Regional Airport 88 km |
| Abraham Lincoln Capital Airport, IL | isd | 0.98 | -0.17 | Decatur Airport 76 km |
| Lrncvll-Vincnes Intl Arpt, IL | isd-linked | 0.99 | -0.68 | Evansville Regional Airport 78 km, Ter Hute Intl-Hulman Fd Ap 79 km, Monroe County Airport 88 km |
| Eastern Iowa Regional Airport, IA | isd | 0.99 | +0.56 | Iowa City Municipal Arpt 44 km, Dubuque Regional Airport 96 km |
| Dupage Airport, IL | isd-linked | 0.99 | +0.36 | Chicago O'Hare International Airport 27 km, Aurora Municipal Airport 32 km, Greater Rockford Airport 73 km |
| Evansville Regional Airport, IN | isd | 0.99 | -0.22 | Lrncvll-Vincnes Intl Arpt 85 km |
| Decatur Airport, IL | isd-linked | 0.99 | -0.15 | Coles County Memo Airport 51 km, Universi Of Il Willard Apt 51 km, Abraham Lincoln Capital Airport 80 km |
| Tri-County Regional Arpt, WI | isd-linked | 0.99 | -0.63 | Dane Co Regional-Truax Field Airport 74 km |
| Coles County Memo Airport, IL | isd-linked | 1.00 | +0.35 | Universi Of Il Willard Apt 59 km, Decatur Airport 65 km, Ter Hute Intl-Hulman Fd Ap 80 km, Lrncvll-Vincnes Intl Arpt 100 km |
| Greater Rockford Airport, IL | isd | 1.00 | -0.49 | Aurora Municipal Airport 68 km, Dupage Airport 73 km, Chicago O'Hare International Airport 94 km |
| Kirksville Regional Arpt, MO | isd-linked | 1.00 | +0.05 | no land station within 100 km |
| Ter Hute Intl-Hulman Fd Ap, IN | isd-linked | 1.00 | +0.16 | Monroe County Airport 67 km, Lrncvll-Vincnes Intl Arpt 88 km, Coles County Memo Airport 88 km |
| Aurora Municipal Airport, IL | isd-linked | 1.00 | -0.29 | Dupage Airport 26 km, Chicago O'Hare International Airport 52 km, Greater Rockford Airport 70 km |
| Scott Air Force Base/Midamerica Airport, IL | isd-linked | 1.00 | +0.04 | St Louis Downtown Airport 35 km, Lambert-St Louis International Ap 61 km, Spirit Of St Louis Airport 81 km, Southern Illinois Airport 91 km |
| Purdue University Airport, IN | isd | 1.00 | -0.60 | no land station within 100 km |
| Universi Of Il Willard Apt, IL | isd-linked | 1.00 | +0.38 | Decatur Airport 56 km, Coles County Memo Airport 58 km |

## Places through the cooling model

The place's cell against the station's own record, p50 per 100 MW: % difference in each design's own water (towers are judged by this one), then hybrid and pads as % of towers' water at the place (judged from model 1.16).

| Place | Station (km) | Cell land | towers avg | towers peak | hybrid avg | hybrid peak | assist avg | assist peak |
|---|---|---|---|---|---|---|---|---|
| Stickney township | Chicago Midway Intl Arpt (2) | 0.82 | -2 | -1 | -42 | -15 | -52 | -22 |
| Benton township | Waukegan Regional Airport (1) | 0.73 | +0 | +2 | +23 | +12 | +25 | +13 |
| De Soto village | Southern Illinois Airport (4) | 0.98 | +0 | -0 | -0 | -0 | +5 | +3 |
| Shiloh Valley township | Scott Air Force Base/Midamerica Airport (3) | 1.00 | +0 | +1 | +8 | +11 | +9 | +15 |
| Springfield township | Abraham Lincoln Capital Airport (2) | 0.98 | -0 | +1 | +1 | +10 | -1 | +7 |
| Burton township | Quincy Rgnl-Bldwn Fld Arpt (5) | 0.98 | -0 | +0 | -5 | +6 | -14 | -11 |
| Bensenville village | Chicago O'Hare International Airport (1) | 0.98 | -0 | -2 | -9 | -10 | -18 | -18 |
| West Chicago city | Dupage Airport (2) | 0.99 | -0 | +1 | -6 | +8 | +3 | +12 |
| Cahokia Heights city | St Louis Downtown Airport (1) | 0.98 | +0 | +1 | -2 | +7 | +2 | +11 |
| Tolono township | Universi Of Il Willard Apt (2) | 1.00 | +1 | +2 | +5 | +22 | +12 | +13 |
| Long Creek township | Decatur Airport (3) | 0.99 | -0 | -1 | -16 | +0 | -13 | -5 |
| Lafayette township | Coles County Memo Airport (2) | 1.00 | -0 | +1 | +10 | +8 | +17 | +12 |

| Place | hybrid avg, % of towers | hybrid peak, % of towers | assist avg, % of towers | assist peak, % of towers |
|---|---|---|---|---|
| Stickney township | -0.89 | -10.66 | -1.03 | -10.72 |
| Benton township | +0.26 | +6.73 | +0.20 | +4.46 |
| De Soto village | -0.01 | -0.21 | +0.15 | +0.92 |
| Shiloh Valley township | +0.25 | +5.43 | +0.28 | +5.72 |
| Springfield township | +0.04 | +4.96 | -0.03 | +2.25 |
| Burton township | -0.11 | +3.11 | -0.31 | -4.44 |
| Bensenville village | -0.18 | -5.95 | -0.29 | -6.81 |
| West Chicago city | -0.11 | +4.00 | +0.04 | +3.87 |
| Cahokia Heights city | -0.08 | +3.46 | +0.07 | +4.55 |
| Tolono township | +0.11 | +9.97 | +0.22 | +3.99 |
| Long Creek township | -0.43 | +0.14 | -0.28 | -1.51 |
| Lafayette township | +0.22 | +3.99 | +0.30 | +3.59 |

A fail is a method question for Andrew; the command changes nothing. Criteria: `waterledger.national.era5_check.CRITERIA`.
