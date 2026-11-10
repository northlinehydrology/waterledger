# ERA5 check: IN

**PASS** (2026-11-10; model 1.11; design 0005's leave-one-station-out check; 35 stations).

| Criterion | Test | Limit | Value | Pass | Limit set from |
|---|---|---|---|---|---|
| W1 | land stations held out, at least | 5 | 32 | yes | too few to judge below this |
| W2 | land cells: median |error| in the 0.4% design dry-bulb, C, at most | 0.75 | 0.26 | yes | four states 0.30-0.68 (Virginia); +0.07 |
| W3 | land cells: |mean error| in the design dry-bulb, C, at most | 0.50 | 0.02 | yes | four states 0.07-0.33 (Texas); +0.17 |
| W4 | land cells: median |error| in the 0.4% wet bulb, C, at most | 0.40 | 0.14 | yes | four states 0.10-0.25 (Virginia); +0.15 |
| W5 | corrected shore cells (3 or more): median |error| in the design dry-bulb, C, at most | 0.50 | - | not judged | four states 0.19-0.32 (Michigan); +0.18 |
| W6 | corrected shore cells (3 or more): median |error| no worse than uncorrected | - | - | not judged | the reason to correct |
| W7 | corrected cells: |mean error| in the 1-in-10-year peak day's mean wet bulb, C, at most | 0.50 | 0.02 | yes | model 1.10 [A]: qm-2's Michigan peak days ran 0.72 C humid, mapping the dew point brought Michigan and Ohio to 0.23 (methods log, Nov 8, 2026) |
| P1 | places sampled, at least | 5 | 9 | yes | too few to judge below this |
| P2 | places: median |difference| in the hybrid average day, %, at most | 8.00 | 3.87 | yes | four states 1.9-4.6 (Virginia); +3.4 |
| P3 | places: |mean difference| in the hybrid average day, %, at most | 6.00 | 0.60 | yes | four states 0.6-4.9 (Virginia); +1.1 |
| P4 | places: median |difference| in the hybrid peak day, %, at most | 6.00 | 3.72 | yes | four states 0.5-3.2 (Virginia); +2.8 |
| P5 | places: median |difference| in towers' average day, %, at most | 2.00 | 0.20 | yes | four states 0.03-0.22; +1.8 |

## Weather at the held-out stations

Median absolute error (mean error), C, against the station on its own hours.

| Stations | Way | Design dry-bulb | 0.4% wet bulb | Summer afternoon T | Mean dew point |
|---|---|---|---|---|---|
| land cells, corrected (32) | uncorrected | 0.30 (-0.30) | 0.16 (-0.20) | 0.22 (-0.17) | 0.21 (-0.07) |
| land cells, corrected (32) | decided | 0.26 (-0.02) | 0.14 (-0.10) | 0.22 (+0.12) | 0.25 (+0.01) |
| shore cells, corrected (2) | uncorrected | 1.80 (-1.80) | 0.17 (-0.17) | 0.87 (-0.87) | 0.53 (+0.53) |
| shore cells, corrected (2) | decided | 1.09 (-0.16) | 0.62 (-0.05) | 2.16 (+0.10) | 0.40 (+0.02) |
| shore cells, no shore station (1) | uncorrected | 1.55 (-1.55) | 0.08 (-0.08) | 0.12 (-0.12) | 0.63 (+0.63) |

| Station | Source | Cell land | Design dry-bulb error (C) | Corrected from |
|---|---|---|---|---|
| Sw Michigan Regional Arpt, MI | isd-linked | 0.65 | -1.55 | no shore station within 100 km |
| Waukegan Regional Airport, IL | isd-linked | 0.73 | +0.92 | Chicago Midway Intl Arpt 82 km |
| Chicago Midway Intl Arpt, IL | isd | 0.82 | -1.25 | Waukegan Regional Airport 76 km |
| Toledo Express Airport, OH | isd | 0.95 | +0.02 | Findlay Airport 54 km, Defiance Memorial Airport 60 km, Lima Allen County Airport 91 km |
| Klmazo/Btl Creek Intl Arpt, MI | isd-linked | 0.97 | -0.25 | W K Kellogg Airport 22 km, Jakson Co-Rynolds Fld Arpt 86 km, South Bend Regional Airport 90 km |
| Louisville Intl-Standiford Field Ap, KY | isd | 0.97 | -0.55 | Bowman Field Airport 8 km, Godman Aaf Airport 43 km, Capital City Airport 74 km |
| Bowman Field Airport, KY | isd-linked | 0.97 | +0.22 | Louisville Intl-Standiford Field Ap 8 km, Godman Aaf Airport 43 km, Capital City Airport 74 km |
| Godman Aaf Airport, KY | isd-linked | 0.97 | +0.53 | Louisville Intl-Standiford Field Ap 31 km, Bowman Field Airport 39 km, Capital City Airport 98 km |
| Chicago O'Hare International Airport, IL | isd | 0.98 | -0.44 | Dupage Airport 24 km, Aurora Municipal Airport 47 km |
| Cincinnati/Northern Kentucky Intl Ap, KY | isd | 0.98 | +0.04 | Cina Muni Apt/Lukn Fd Apt 31 km, Capital City Airport 92 km, Airborne Airpark Airport 97 km |
| Cina Muni Apt/Lukn Fd Apt, OH | isd | 0.98 | -0.26 | Cincinnati/Northern Kentucky Intl Ap 16 km, Airborne Airpark Airport 79 km, Capital City Airport 97 km |
| Monroe County Airport, IN | isd-linked | 0.98 | +0.15 | Indianapolis International Airport 56 km, Ter Hute Intl-Hulman Fd Ap 74 km |
| W K Kellogg Airport, MI | isd-linked | 0.98 | +0.01 | Klmazo/Btl Creek Intl Arpt 24 km, Jakson Co-Rynolds Fld Arpt 65 km |
| Lrncvll-Vincnes Intl Arpt, IL | isd-linked | 0.99 | -0.68 | Evansville Regional Airport 78 km, Ter Hute Intl-Hulman Fd Ap 79 km, Monroe County Airport 88 km |
| Jakson Co-Rynolds Fld Arpt, MI | isd | 0.99 | +0.30 | W K Kellogg Airport 61 km, Klmazo/Btl Creek Intl Arpt 86 km, Toledo Express Airport 94 km |
| Dupage Airport, IL | isd-linked | 0.99 | +0.35 | Chicago O'Hare International Airport 27 km, Aurora Municipal Airport 32 km |
| South Bend Regional Airport, IN | isd | 0.99 | +0.14 | Klmazo/Btl Creek Intl Arpt 79 km |
| Evansville Regional Airport, IN | isd | 0.99 | -0.22 | Lrncvll-Vincnes Intl Arpt 85 km |
| Wright-Patterson Afb Airport, OH | isd-linked | 0.99 | -0.40 | J.M.Cox Dayton International Airport 26 km, Airborne Airpark Airport 40 km, Cina Muni Apt/Lukn Fd Apt 80 km, Cincinnati/Northern Kentucky Intl Ap 98 km |
| Coles County Memo Airport, IL | isd-linked | 1.00 | +0.22 | Universi Of Il Willard Apt 59 km, Ter Hute Intl-Hulman Fd Ap 80 km, Lrncvll-Vincnes Intl Arpt 100 km |
| Blue Grass Airport, KY | isd | 1.00 | -0.34 | Capital City Airport 41 km |
| Indianapolis International Airport, IN | isd | 1.00 | -0.06 | Monroe County Airport 74 km, Delaware Co-Johnson Fd Apt 91 km, Purdue University Airport 94 km, Ter Hute Intl-Hulman Fd Ap 98 km |
| Airborne Airpark Airport, OH | isd-linked | 1.00 | +0.26 | Wright-Patterson Afb Airport 45 km, J.M.Cox Dayton International Airport 60 km, Cina Muni Apt/Lukn Fd Apt 72 km, Cincinnati/Northern Kentucky Intl Ap 94 km |
| Lima Allen County Airport, OH | isd-linked | 1.00 | +0.36 | Findlay Airport 40 km, Defiance Memorial Airport 74 km, Toledo Express Airport 94 km, J.M.Cox Dayton International Airport 96 km |
| Ter Hute Intl-Hulman Fd Ap, IN | isd-linked | 1.00 | +0.10 | Monroe County Airport 67 km, Indianapolis International Airport 87 km, Lrncvll-Vincnes Intl Arpt 88 km, Coles County Memo Airport 88 km |
| Aurora Municipal Airport, IL | isd-linked | 1.00 | -0.33 | Dupage Airport 26 km, Chicago O'Hare International Airport 52 km |
| Fort Wayne International Airport, IN | isd | 1.00 | -0.37 | Defiance Memorial Airport 78 km, Grissom Afb Airport 85 km, Delaware Co-Johnson Fd Apt 86 km |
| J.M.Cox Dayton International Airport, OH | isd | 1.00 | +0.35 | Wright-Patterson Afb Airport 25 km, Airborne Airpark Airport 75 km, Lima Allen County Airport 81 km |
| Findlay Airport, OH | isd | 1.00 | -0.25 | Lima Allen County Airport 40 km, Toledo Express Airport 65 km, Defiance Memorial Airport 68 km |
| Defiance Memorial Airport, OH | isd-linked | 1.00 | +0.04 | Fort Wayne International Airport 67 km, Toledo Express Airport 69 km, Lima Allen County Airport 72 km, Findlay Airport 74 km |
| Capital City Airport, KY | isd-linked | 1.00 | +0.25 | Blue Grass Airport 42 km, Bowman Field Airport 58 km, Louisville Intl-Standiford Field Ap 64 km, Cincinnati/Northern Kentucky Intl Ap 93 km |
| Grissom Afb Airport, IN | isd-linked | 1.00 | +0.61 | Purdue University Airport 70 km, Fort Wayne International Airport 91 km, Delaware Co-Johnson Fd Apt 92 km |
| Delaware Co-Johnson Fd Apt, IN | isd-linked | 1.00 | +0.08 | Grissom Afb Airport 71 km, Fort Wayne International Airport 84 km, Indianapolis International Airport 89 km |
| Purdue University Airport, IN | isd | 1.00 | -0.53 | Grissom Afb Airport 74 km |
| Universi Of Il Willard Apt, IL | isd-linked | 1.00 | +0.10 | Coles County Memo Airport 58 km |

## Places through the cooling model

The place's cell against the station's own record, p50 per 100 MW, % difference.

| Place | Station (km) | Cell land | towers avg | towers peak | hybrid avg | hybrid peak | assist avg | assist peak |
|---|---|---|---|---|---|---|---|---|
| Center township | Evansville Regional Airport (2) | 0.99 | -1 | +0 | -5 | +3 | -8 | +2 |
| Lost Creek township | Ter Hute Intl-Hulman Fd Ap (4) | 1.00 | +0 | +1 | +4 | +6 | +5 | +12 |
| Van Buren township | Monroe County Airport (2) | 0.99 | +0 | +1 | +3 | +9 | +5 | +13 |
| Decatur township | Indianapolis International Airport (5) | 1.00 | -0 | -0 | -4 | -2 | -8 | -3 |
| West Lafayette city | Purdue University Airport (4) | 1.00 | -0 | +0 | -3 | +3 | -12 | -4 |
| Pleasant township | Fort Wayne International Airport (4) | 1.00 | +0 | +0 | +12 | +2 | +6 | +3 |
| Bunker Hill town | Grissom Afb Airport (4) | 1.00 | -0 | +1 | +2 | +8 | +12 | +10 |
| Delaware County | Delaware Co-Johnson Fd Apt (1) | 1.00 | -0 | +0 | -14 | -4 | -18 | -9 |
| German township | South Bend Regional Airport (2) | 0.99 | -0 | -0 | -0 | +4 | +4 | +6 |

A fail is a method question for Andrew; the command changes nothing. Criteria: `waterledger.national.era5_check.CRITERIA`.
