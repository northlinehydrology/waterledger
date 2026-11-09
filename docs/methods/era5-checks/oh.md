# ERA5 check: OH

**PASS** (2026-11-08; model 1.10; design 0005's leave-one-station-out check; 41 stations).

| Criterion | Test | Limit | Value | Pass | Limit set from |
|---|---|---|---|---|---|
| W1 | land stations held out, at least | 5 | 33 | yes | too few to judge below this |
| W2 | land cells: median |error| in the 0.4% design dry-bulb, C, at most | 0.75 | 0.26 | yes | four states 0.30-0.68 (Virginia); +0.07 |
| W3 | land cells: |mean error| in the design dry-bulb, C, at most | 0.50 | 0.04 | yes | four states 0.07-0.33 (Texas); +0.17 |
| W4 | land cells: median |error| in the 0.4% wet bulb, C, at most | 0.40 | 0.13 | yes | four states 0.10-0.25 (Virginia); +0.15 |
| W5 | corrected shore cells (3 or more): median |error| in the design dry-bulb, C, at most | 0.50 | 0.35 | yes | four states 0.19-0.32 (Michigan); +0.18 |
| W6 | corrected shore cells (3 or more): median |error| no worse than uncorrected | - | 0.35 vs 0.95 | yes | the reason to correct |
| W7 | corrected cells: |mean error| in the 1-in-10-year peak day's mean wet bulb, C, at most | 0.50 | 0.16 | yes | model 1.10 [A]: qm-2's Michigan peak days ran 0.72 C humid, mapping the dew point brought Michigan and Ohio to 0.23 (methods log, Nov 8, 2026) |
| P1 | places sampled, at least | 5 | 12 | yes | too few to judge below this |
| P2 | places: median |difference| in the hybrid average day, %, at most | 8.00 | 2.46 | yes | four states 1.9-4.6 (Virginia); +3.4 |
| P3 | places: |mean difference| in the hybrid average day, %, at most | 6.00 | 1.56 | yes | four states 0.6-4.9 (Virginia); +1.1 |
| P4 | places: median |difference| in the hybrid peak day, %, at most | 6.00 | 5.10 | yes | four states 0.5-3.2 (Virginia); +2.8 |
| P5 | places: median |difference| in towers' average day, %, at most | 2.00 | 0.22 | yes | four states 0.03-0.22; +1.8 |

## Weather at the held-out stations

Median absolute error (mean error), C, against the station on its own hours.

| Stations | Way | Design dry-bulb | 0.4% wet bulb | Summer afternoon T | Mean dew point |
|---|---|---|---|---|---|
| land cells, corrected (33) | uncorrected | 0.30 (-0.30) | 0.16 (-0.03) | 0.22 (-0.16) | 0.19 (+0.11) |
| land cells, corrected (33) | decided | 0.26 (+0.04) | 0.13 (-0.07) | 0.25 (+0.13) | 0.21 (+0.01) |
| shore cells, corrected (7) | uncorrected | 0.95 (-0.93) | 0.15 (-0.19) | 0.59 (-0.46) | 0.44 (+0.44) |
| shore cells, corrected (7) | decided | 0.35 (-0.06) | 0.08 (-0.01) | 0.77 (+0.02) | 0.33 (+0.05) |
| shore cells, no shore station (1) | uncorrected | 2.25 (-2.25) | 0.06 (+0.06) | 1.21 (-1.21) | 1.18 (+1.18) |

| Station | Source | Cell land | Design dry-bulb error (C) | Corrected from |
|---|---|---|---|---|
| Selfridge Air National Guard Base, MI | isd-linked | 0.62 | +0.29 | Detroit City Airport 24 km, Windsor A 30 km, Detroit Metro Wayne County Airport 56 km |
| Cleveland-Hopkins International Ap, OH | isd | 0.65 | -1.06 | Cleveland Burke Lakefnt Ap 7 km, Lorain County Rgnl Airport 40 km |
| Cleveland Burke Lakefnt Ap, OH | isd-linked | 0.65 | +0.44 | Cleveland-Hopkins International Ap 14 km, Lorain County Rgnl Airport 40 km |
| Erie Intl/T. Ridge Field Airport, PA | isd | 0.72 | -2.25 | no shore station within 100 km |
| Windsor A, Ontario | eccc | 0.78 | +0.58 | Detroit City Airport 18 km, Detroit Metro Wayne County Airport 27 km, Selfridge Air National Guard Base 42 km |
| Lorain County Rgnl Airport, OH | isd-linked | 0.81 | -0.35 | Cleveland-Hopkins International Ap 38 km, Cleveland Burke Lakefnt Ap 57 km |
| Detroit City Airport, MI | isd | 0.88 | -0.21 | Selfridge Air National Guard Base 19 km, Windsor A 25 km, Detroit Metro Wayne County Airport 40 km |
| Detroit Metro Wayne County Airport, MI | isd | 0.88 | -0.10 | Windsor A 24 km, Detroit City Airport 26 km, Selfridge Air National Guard Base 53 km |
| Toledo Express Airport, OH | isd | 0.95 | +0.12 | Metcalf Field Airport 24 km, Findlay Airport 54 km, Defiance Memorial Airport 60 km, Willow Run Airport 84 km |
| Metcalf Field Airport, OH | isd-linked | 0.96 | +0.08 | Toledo Express Airport 27 km, Findlay Airport 56 km, Defiance Memorial Airport 80 km, Willow Run Airport 82 km |
| Klmazo/Btl Creek Intl Arpt, MI | isd-linked | 0.97 | -0.26 | W K Kellogg Airport 22 km, Jakson Co-Rynolds Fld Arpt 86 km |
| Cincinnati/Northern Kentucky Intl Ap, KY | isd | 0.98 | +0.04 | Cina Muni Apt/Lukn Fd Apt 31 km, Capital City Airport 92 km, Airborne Airpark Airport 97 km |
| Cina Muni Apt/Lukn Fd Apt, OH | isd | 0.98 | -0.26 | Cincinnati/Northern Kentucky Intl Ap 16 km, Airborne Airpark Airport 79 km, Capital City Airport 97 km |
| Parkersburg/Mid-Ohio Valley Regional Airport, WV | isd | 0.98 | -0.13 | Zanesville Municipal Arpt 84 km, Yeager Airport 97 km |
| W K Kellogg Airport, MI | isd-linked | 0.98 | +0.01 | Klmazo/Btl Creek Intl Arpt 24 km, Jakson Co-Rynolds Fld Arpt 65 km |
| Wheeling Ohio County Arpt, WV | isd-linked | 0.99 | +0.82 | Pittsburgh International Airport 52 km, Allegheny County Airport 71 km, Akron-Canton Regional Airport 95 km, Mgtn Rgnl-W L B Hart Fd Ap 97 km |
| Pittsburgh International Airport, PA | isd | 0.99 | +0.12 | Allegheny County Airport 32 km, Wheeling Ohio County Arpt 50 km, Youngstown-Warren Regional Airport 91 km, Mgtn Rgnl-W L B Hart Fd Ap 99 km |
| Allegheny County Airport, PA | isd | 0.99 | +0.09 | Pittsburgh International Airport 32 km, Wheeling Ohio County Arpt 55 km, Mgtn Rgnl-W L B Hart Fd Ap 67 km |
| Jakson Co-Rynolds Fld Arpt, MI | isd | 0.99 | +0.47 | W K Kellogg Airport 61 km, Willow Run Airport 80 km, Klmazo/Btl Creek Intl Arpt 86 km, Toledo Express Airport 94 km |
| Akron-Canton Regional Airport, OH | isd | 0.99 | -0.33 | Youngstown-Warren Regional Airport 75 km, Mansfield Lahm Regional Airport 88 km |
| Tri-State/M.J.Fergus, WV | isd | 0.99 | -0.27 | Yeager Airport 81 km |
| Willow Run Airport, MI | isd-linked | 0.99 | -0.69 | Metcalf Field Airport 76 km, Toledo Express Airport 78 km, Jakson Co-Rynolds Fld Arpt 79 km |
| Mgtn Rgnl-W L B Hart Fd Ap, WV | isd | 0.99 | -0.12 | Harrison/Marion Rgnl Arpt 53 km, Allegheny County Airport 68 km, Wheeling Ohio County Arpt 72 km, Pittsburgh International Airport 84 km |
| Youngstown-Warren Regional Airport, OH | isd | 0.99 | +0.91 | Akron-Canton Regional Airport 69 km, Pittsburgh International Airport 96 km |
| Port Columbus International Airport, OH | isd | 0.99 | -0.46 | Ohio State University Arpt 11 km, Fairfield County Airport 40 km, Wright-Patterson Afb Airport 92 km, Airborne Airpark Airport 92 km |
| Ohio State University Arpt, OH | isd-linked | 0.99 | +0.44 | Port Columbus International Airport 10 km, Fairfield County Airport 40 km, Wright-Patterson Afb Airport 92 km, Airborne Airpark Airport 92 km |
| Mansfield Lahm Regional Airport, OH | isd-linked | 0.99 | +0.76 | Ohio State University Arpt 89 km, Port Columbus International Airport 90 km, Akron-Canton Regional Airport 91 km |
| Wright-Patterson Afb Airport, OH | isd-linked | 0.99 | -0.40 | J.M.Cox Dayton International Airport 26 km, Airborne Airpark Airport 40 km, Cina Muni Apt/Lukn Fd Apt 80 km, Ohio State University Arpt 87 km |
| Yeager Airport, WV | isd | 0.99 | -0.30 | Tri-State/M.J.Fergus 93 km, Parkersburg/Mid-Ohio Valley Regional Airport 93 km |
| Zanesville Municipal Arpt, OH | isd | 1.00 | +0.13 | Fairfield County Airport 63 km, Port Columbus International Airport 75 km, Parkersburg/Mid-Ohio Valley Regional Airport 88 km, Ohio State University Arpt 92 km |
| Blue Grass Airport, KY | isd | 1.00 | -0.34 | Capital City Airport 41 km |
| Airborne Airpark Airport, OH | isd-linked | 1.00 | +0.20 | Wright-Patterson Afb Airport 45 km, J.M.Cox Dayton International Airport 60 km, Cina Muni Apt/Lukn Fd Apt 72 km, Ohio State University Arpt 86 km |
| Lima Allen County Airport, OH | isd-linked | 1.00 | +0.36 | Findlay Airport 40 km, Defiance Memorial Airport 74 km, Toledo Express Airport 94 km, J.M.Cox Dayton International Airport 96 km |
| Harrison/Marion Rgnl Arpt, WV | isd-linked | 1.00 | -0.06 | Mgtn Rgnl-W L B Hart Fd Ap 53 km |
| Fort Wayne International Airport, IN | isd | 1.00 | -0.29 | Defiance Memorial Airport 78 km, Delaware Co-Johnson Fd Apt 86 km |
| Fairfield County Airport, OH | isd-linked | 1.00 | +0.41 | Port Columbus International Airport 29 km, Ohio State University Arpt 46 km, Zanesville Municipal Arpt 76 km, Airborne Airpark Airport 95 km |
| J.M.Cox Dayton International Airport, OH | isd | 1.00 | +0.35 | Wright-Patterson Afb Airport 25 km, Airborne Airpark Airport 75 km, Lima Allen County Airport 81 km |
| Findlay Airport, OH | isd | 1.00 | -0.23 | Lima Allen County Airport 40 km, Toledo Express Airport 65 km, Metcalf Field Airport 67 km, Defiance Memorial Airport 68 km |
| Defiance Memorial Airport, OH | isd-linked | 1.00 | +0.04 | Fort Wayne International Airport 67 km, Toledo Express Airport 69 km, Lima Allen County Airport 72 km, Findlay Airport 74 km |
| Capital City Airport, KY | isd-linked | 1.00 | +0.18 | Blue Grass Airport 42 km, Cincinnati/Northern Kentucky Intl Ap 93 km |
| Delaware Co-Johnson Fd Apt, IN | isd-linked | 1.00 | +0.07 | Fort Wayne International Airport 84 km |

## Places through the cooling model

The place's cell against the station's own record, p50 per 100 MW, % difference.

| Place | Station (km) | Cell land | towers avg | towers peak | hybrid avg | hybrid peak | assist avg | assist peak |
|---|---|---|---|---|---|---|---|---|
| New Russia township | Lorain County Rgnl Airport (4) | 0.81 | +0 | +1 | +3 | +9 | -3 | +1 |
| Brook Park city | Cleveland-Hopkins International Ap (3) | 0.65 | +0 | +1 | +2 | +15 | -10 | +6 |
| Madison township | Mansfield Lahm Regional Airport (4) | 0.99 | +1 | +2 | +12 | +5 | +14 | +10 |
| Whitehall city | Port Columbus International Airport (2) | 0.99 | -0 | -0 | -4 | +4 | -10 | +3 |
| Perry township | Zanesville Municipal Arpt (4) | 1.00 | +0 | +0 | +5 | +5 | +3 | +11 |
| Lake township | Metcalf Field Airport (2) | 0.96 | -0 | +0 | -1 | +4 | -2 | +1 |
| Vandalia city | J.M.Cox Dayton International Airport (4) | 1.00 | -0 | +1 | -5 | +2 | -7 | -2 |
| Greenfield township | Fairfield County Airport (3) | 1.00 | +0 | +1 | +5 | +8 | +9 | +12 |
| Clinton County | Airborne Airpark Airport (2) | 1.00 | -0 | +1 | +2 | +7 | +2 | +3 |
| Fairfax village | Cina Muni Apt/Lukn Fd Apt (4) | 0.99 | -0 | -0 | +2 | +8 | +4 | +5 |
| Perry township | Lima Allen County Airport (4) | 1.00 | -0 | -0 | -0 | +0 | +2 | +0 |
| Green city | Akron-Canton Regional Airport (5) | 0.99 | -0 | +1 | -1 | +4 | -6 | +1 |

A fail is a method question for Andrew; the command changes nothing. Criteria: `waterledger.national.era5_check.CRITERIA`.
