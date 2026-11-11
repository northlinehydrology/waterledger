# ERA5 check: MN

**PASS** (2026-11-11; model 1.11; design 0005's leave-one-station-out check; 31 stations).

| Criterion | Test | Limit | Value | Pass | Limit set from |
|---|---|---|---|---|---|
| W1 | land stations held out, at least | 5 | 28 | yes | too few to judge below this |
| W2 | land cells: median |error| in the 0.4% design dry-bulb, C, at most | 0.75 | 0.40 | yes | four states 0.30-0.68 (Virginia); +0.07 |
| W3 | land cells: |mean error| in the design dry-bulb, C, at most | 0.50 | 0.29 | yes | four states 0.07-0.33 (Texas); +0.17 |
| W4 | land cells: median |error| in the 0.4% wet bulb, C, at most | 0.40 | 0.22 | yes | four states 0.10-0.25 (Virginia); +0.15 |
| W5 | corrected shore cells (3 or more): median |error| in the design dry-bulb, C, at most | 0.50 | - | not judged | four states 0.19-0.32 (Michigan); +0.18 |
| W6 | corrected shore cells (3 or more): median |error| no worse than uncorrected | - | - | not judged | the reason to correct |
| W7 | corrected cells: |mean error| in the 1-in-10-year peak day's mean wet bulb, C, at most | 0.50 | 0.06 | yes | model 1.10 [A]: qm-2's Michigan peak days ran 0.72 C humid, mapping the dew point brought Michigan and Ohio to 0.23 (methods log, Nov 8, 2026) |
| P1 | places sampled, at least | 5 | 12 | yes | too few to judge below this |
| P2 | places: median |difference| in the hybrid average day, %, at most | 8.00 | 5.72 | yes | four states 1.9-4.6 (Virginia); +3.4 |
| P3 | places: |mean difference| in the hybrid average day, %, at most | 6.00 | 3.61 | yes | four states 0.6-4.9 (Virginia); +1.1 |
| P4 | places: median |difference| in the hybrid peak day, %, at most | 6.00 | 4.35 | yes | four states 0.5-3.2 (Virginia); +2.8 |
| P5 | places: median |difference| in towers' average day, %, at most | 2.00 | 0.25 | yes | four states 0.03-0.22; +1.8 |

## Weather at the held-out stations

Median absolute error (mean error), C, against the station on its own hours.

| Stations | Way | Design dry-bulb | 0.4% wet bulb | Summer afternoon T | Mean dew point |
|---|---|---|---|---|---|
| land cells, corrected (18) | uncorrected | 0.63 (-0.49) | 0.15 (-0.12) | 0.28 (-0.25) | 0.21 (+0.07) |
| land cells, corrected (18) | decided | 0.32 (-0.14) | 0.23 (-0.01) | 0.30 (+0.02) | 0.32 (+0.09) |
| land cells, no station (10) | uncorrected | 0.68 (-0.56) | 0.20 (-0.26) | 0.48 (-0.39) | 0.14 (+0.05) |
| shore cells, no shore station (3) | uncorrected | 1.50 (-1.40) | 0.51 (-0.24) | 0.87 (-0.73) | 0.70 (+0.65) |

| Station | Source | Cell land | Design dry-bulb error (C) | Corrected from |
|---|---|---|---|---|
| Duluth International Airport, MN | isd | 0.81 | -1.00 | no shore station within 100 km |
| Atikokan (Aut), Ontario | eccc | 0.84 | -1.50 | no shore station within 100 km |
| Brainerd Lakes Rgnl Arpt, MN | isd-linked | 0.84 | -1.70 | no shore station within 100 km |
| Sprague, Manitoba | eccc | 0.91 | +0.36 | Baudette International Apt 72 km |
| Sawyer County Airport, WI | isd-linked | 0.92 | -0.85 | no land station within 100 km |
| St Paul Dwtwn Holman Fd Ap, MN | isd-linked | 0.93 | -0.17 | Minneapolis-St Paul International Ap 22 km, Crystal Airport 28 km, Flying Cloud Airport 42 km |
| Chandler Field Airport, MN | isd | 0.93 | +0.81 | Appleton Municipal Airport 70 km |
| Falls International Airport, MN | isd | 0.94 | +0.28 | Baudette International Apt 86 km |
| Pk Rpds Muni-Konshok Fd Ap, MN | isd | 0.94 | -1.05 | no land station within 100 km |
| Watertown Municipal Arpt, SD | isd | 0.94 | -0.75 | no land station within 100 km |
| Minneapolis-St Paul International Ap, MN | isd | 0.94 | -0.45 | Crystal Airport 10 km, St Paul Dwtwn Holman Fd Ap 17 km, Flying Cloud Airport 26 km, St Cloud Regional Airport 87 km |
| Crystal Airport, MN | isd-linked | 0.94 | -0.26 | Minneapolis-St Paul International Ap 13 km, St Paul Dwtwn Holman Fd Ap 17 km, Flying Cloud Airport 26 km, St Cloud Regional Airport 87 km |
| St Cloud Regional Airport, MN | isd | 0.95 | +0.03 | Crystal Airport 70 km, Flying Cloud Airport 85 km, Minneapolis-St Paul International Ap 91 km, St Paul Dwtwn Holman Fd Ap 97 km |
| Flying Cloud Airport, MN | isd-linked | 0.96 | -0.27 | Minneapolis-St Paul International Ap 26 km, Crystal Airport 37 km, St Paul Dwtwn Holman Fd Ap 40 km, St Cloud Regional Airport 98 km |
| Appleton Municipal Airport, MN | isd-linked | 0.96 | -0.16 | Chandler Field Airport 83 km, Watertown Municipal Arpt 98 km |
| La Crosse Municipal Airport, WI | isd | 0.96 | -1.28 | Chippewa Valley Rgnl Arpt 98 km, Rochester International Airport 100 km |
| Baudette International Apt, MN | isd | 0.97 | -0.52 | Falls International Airport 84 km, Sprague 86 km |
| Spencer Municipal Airport, IA | isd-linked | 0.97 | -1.47 | Estherville Muni Airport 44 km |
| Chisholm-Hibbing Airport, MN | isd | 0.97 | -0.00 | no land station within 100 km |
| Mason City Municipal Arpt, IA | isd | 0.98 | -0.95 | Rochester International Airport 95 km |
| Chippewa Valley Rgnl Arpt, WI | isd | 0.99 | +0.39 | La Crosse Municipal Airport 99 km |
| Estherville Muni Airport, IA | isd-linked | 0.99 | +1.29 | Spencer Municipal Airport 52 km |
| Tri-County Regional Arpt, WI | isd-linked | 0.99 | -0.65 | no land station within 100 km |
| Hector International Airport, ND | isd | 1.00 | -0.40 | no land station within 100 km |
| Redwood Falls Muni Airport, MN | isd-linked | 1.00 | -0.20 | no land station within 100 km |
| Grand Forks Afb Airport, ND | isd-linked | 1.00 | -0.90 | no land station within 100 km |
| Rochester International Airport, MN | isd | 1.00 | -0.10 | no land station within 100 km |
| Carman U Of M Cs, Manitoba | eccc | 1.00 | -0.20 | Gretna (Aut) 61 km, Emerson Auto 78 km |
| Joe Foss Field Airport, SD | isd | 1.00 | -0.70 | no land station within 100 km |
| Gretna (Aut), Manitoba | eccc | 1.00 | +0.07 | Emerson Auto 19 km, Carman U Of M Cs 68 km |
| Emerson Auto, Manitoba | eccc | 1.00 | +0.01 | Gretna (Aut) 23 km, Carman U Of M Cs 79 km |

## Places through the cooling model

The place's cell against the station's own record, p50 per 100 MW, % difference.

| Place | Station (km) | Cell land | towers avg | towers peak | hybrid avg | hybrid peak | assist avg | assist peak |
|---|---|---|---|---|---|---|---|---|
| Hermantown city | Duluth International Airport (7) | 0.81 | +1 | +1 | +7 | +11 | -11 | -14 |
| High Forest township | Rochester International Airport (4) | 1.00 | +0 | +1 | +11 | +5 | +9 | +8 |
| Appleton city | Appleton Municipal Airport (3) | 0.96 | +0 | -0 | +6 | +8 | +9 | +4 |
| Haven township | St Cloud Regional Airport (3) | 0.95 | +1 | +1 | +17 | +9 | +13 | +9 |
| Oak Lawn township | Brainerd Lakes Rgnl Arpt (3) | 0.95 | +0 | +0 | +2 | -3 | +1 | -3 |
| Redwood Falls city | Redwood Falls Muni Airport (2) | 1.00 | +0 | +0 | +6 | +6 | +1 | +2 |
| Alexandria city | Chandler Field Airport (2) | 0.92 | +0 | +0 | +6 | -2 | +5 | -1 |
| Brooklyn Center city | Crystal Airport (3) | 0.94 | +0 | +0 | -1 | -0 | -5 | -4 |
| Eden Prairie city | Flying Cloud Airport (2) | 0.96 | -0 | +1 | -3 | +4 | -5 | +3 |
| Richfield city | Minneapolis-St Paul International Ap (4) | 0.96 | -0 | -0 | -5 | -2 | -11 | -5 |
| West St. Paul city | St Paul Dwtwn Holman Fd Ap (4) | 0.93 | -0 | +0 | +5 | +5 | +3 | +5 |
| Park Rapids city | Pk Rpds Muni-Konshok Fd Ap (2) | 0.94 | -0 | -1 | -6 | -2 | -15 | -3 |

A fail is a method question for Andrew; the command changes nothing. Criteria: `waterledger.national.era5_check.CRITERIA`.
