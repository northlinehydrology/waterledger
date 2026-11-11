# ERA5 check: PA

**FAIL** (2026-11-11; model 1.11; design 0005's leave-one-station-out check; 48 stations).

| Criterion | Test | Limit | Value | Pass | Limit set from |
|---|---|---|---|---|---|
| W1 | land stations held out, at least | 5 | 38 | yes | too few to judge below this |
| W2 | land cells: median |error| in the 0.4% design dry-bulb, C, at most | 0.75 | 0.21 | yes | four states 0.30-0.68 (Virginia); +0.07 |
| W3 | land cells: |mean error| in the design dry-bulb, C, at most | 0.50 | 0.06 | yes | four states 0.07-0.33 (Texas); +0.17 |
| W4 | land cells: median |error| in the 0.4% wet bulb, C, at most | 0.40 | 0.37 | yes | four states 0.10-0.25 (Virginia); +0.15 |
| W5 | corrected shore cells (3 or more): median |error| in the design dry-bulb, C, at most | 0.50 | 0.85 | **no** | four states 0.19-0.32 (Michigan); +0.18 |
| W6 | corrected shore cells (3 or more): median |error| no worse than uncorrected | - | 0.85 vs 1.35 | yes | the reason to correct |
| W7 | corrected cells: |mean error| in the 1-in-10-year peak day's mean wet bulb, C, at most | 0.50 | 0.03 | yes | model 1.10 [A]: qm-2's Michigan peak days ran 0.72 C humid, mapping the dew point brought Michigan and Ohio to 0.23 (methods log, Nov 8, 2026) |
| P1 | places sampled, at least | 5 | 12 | yes | too few to judge below this |
| P2 | places: median |difference| in the hybrid average day, %, at most | 8.00 | 10.87 | **no** | four states 1.9-4.6 (Virginia); +3.4 |
| P3 | places: |mean difference| in the hybrid average day, %, at most | 6.00 | 4.09 | yes | four states 0.6-4.9 (Virginia); +1.1 |
| P4 | places: median |difference| in the hybrid peak day, %, at most | 6.00 | 3.73 | yes | four states 0.5-3.2 (Virginia); +2.8 |
| P5 | places: median |difference| in towers' average day, %, at most | 2.00 | 0.59 | yes | four states 0.03-0.22; +1.8 |

## Weather at the held-out stations

Median absolute error (mean error), C, against the station on its own hours.

| Stations | Way | Design dry-bulb | 0.4% wet bulb | Summer afternoon T | Mean dew point |
|---|---|---|---|---|---|
| land cells, corrected (35) | uncorrected | 0.45 (-0.09) | 0.32 (-0.11) | 0.31 (-0.06) | 0.26 (+0.07) |
| land cells, corrected (35) | decided | 0.22 (-0.02) | 0.37 (-0.13) | 0.36 (-0.01) | 0.28 (-0.00) |
| land cells, no station (3) | uncorrected | 0.10 (-0.45) | 0.31 (-0.12) | 0.37 (-0.47) | 0.32 (-0.02) |
| shore cells, corrected (8) | uncorrected | 1.35 (-1.35) | 0.23 (+0.03) | 0.58 (-0.56) | 1.33 (+1.06) |
| shore cells, corrected (8) | decided | 0.85 (+0.05) | 0.31 (+0.15) | 0.65 (+0.19) | 0.08 (+0.01) |
| shore cells, no shore station (2) | uncorrected | 1.60 (-1.60) | 0.10 (-0.04) | 0.61 (-0.59) | 0.83 (+0.83) |

| Station | Source | Cell land | Design dry-bulb error (C) | Corrected from |
|---|---|---|---|---|
| John F Kennedy International Airport, NY | isd | 0.58 | +1.20 | La Guardia Airport 11 km, Central Park 19 km, Teterboro Airport 28 km, Westchester County Airport 35 km |
| Cleveland Burke Lakefnt Ap, OH | isd-linked | 0.65 | -0.95 | no shore station within 100 km |
| Millville Municipal Arpt, NJ | isd | 0.69 | +0.36 | Atlantic City International Airport 44 km |
| La Guardia Airport, NY | isd | 0.71 | -0.90 | Central Park 4 km, Teterboro Airport 13 km, Newark Liberty International Ap 16 km, John F Kennedy International Airport 23 km |
| Central Park, NY | isd-linked | 0.71 | +0.79 | La Guardia Airport 11 km, Teterboro Airport 13 km, Newark Liberty International Ap 16 km, John F Kennedy International Airport 23 km |
| Teterboro Airport, NJ | isd-linked | 0.71 | -0.81 | Central Park 4 km, La Guardia Airport 11 km, Newark Liberty International Ap 16 km, John F Kennedy International Airport 23 km |
| Erie Intl/T. Ridge Field Airport, PA | isd | 0.72 | -2.25 | no shore station within 100 km |
| Westchester County Airport, NY | isd | 0.76 | +1.28 | La Guardia Airport 27 km, Teterboro Airport 30 km, Central Park 31 km, John F Kennedy International Airport 40 km |
| Atlantic City International Airport, NJ | isd | 0.81 | +0.04 | Millville Municipal Arpt 52 km |
| Newark Liberty International Ap, NJ | isd | 0.82 | -1.55 | Teterboro Airport 20 km, Central Park 24 km, La Guardia Airport 31 km, John F Kennedy International Airport 43 km |
| Dover Afb Airport, DE | isd-linked | 0.92 | +0.17 | Wilmington Airport 48 km, Philadelphia International Airport 73 km, South Jersey Regional Arpt 95 km |
| Wilmington Airport, DE | isd-linked | 0.93 | +0.46 | Philadelphia International Airport 27 km, Ne Philadelphia Airport 55 km, South Jersey Regional Arpt 60 km, Dover Afb Airport 69 km |
| Ithaca Tompkins Regional Airport, NY | isd-linked | 0.94 | -0.05 | Elmira/Corning Rgnl Arpt 50 km, Greater Binghamton/E A Link Field Ap 54 km |
| Philadelphia International Airport, PA | isd | 0.94 | -0.17 | Wilmington Airport 32 km, South Jersey Regional Arpt 41 km, Ne Philadelphia Airport 42 km, Mcguire Afb Airport 63 km |
| Baltimore-Washington Intl Airport, MD | isd | 0.94 | -0.48 | Ronald Reagan Washington Natl Ap 51 km, Washington Dulles International Ap 70 km, York Airport 75 km, Hgrtwn Rgnl-R.Hnson Fld Ap 98 km |
| Ronald Reagan Washington Natl Ap, VA | isd | 0.94 | -0.06 | Washington Dulles International Ap 44 km, Baltimore-Washington Intl Airport 54 km |
| Ne Philadelphia Airport, PA | isd-linked | 0.96 | -0.13 | South Jersey Regional Arpt 15 km, Philadelphia International Airport 24 km, Mcguire Afb Airport 34 km, Trenton Mercer Airport 34 km |
| Mcguire Afb Airport, NJ | isd-linked | 0.96 | -0.15 | South Jersey Regional Arpt 30 km, Trenton Mercer Airport 41 km, Ne Philadelphia Airport 44 km, Philadelphia International Airport 64 km |
| Essex County Airport, NJ | isd-linked | 0.97 | -0.66 | Dutchess County Airport 76 km, Trenton Mercer Airport 94 km |
| South Jersey Regional Arpt, NJ | isd-linked | 0.97 | +0.15 | Mcguire Afb Airport 13 km, Ne Philadelphia Airport 24 km, Trenton Mercer Airport 31 km, Philadelphia International Airport 43 km |
| Altoona-Blair County Arpt, PA | isd | 0.97 | +0.10 | J Murtha Jtwn-Cmbra Co Apt 50 km, Hgrtwn Rgnl-R.Hnson Fld Ap 75 km, Etrn Wv Rgnl/Shpherd Fd Ap 97 km |
| Lancaster Airport, PA | isd-linked | 0.97 | +0.20 | Rdng Rgnl/C A Spaatz Fd Ap 48 km, Harrisburg International Airport 50 km, York Airport 54 km, Capital City Airport 57 km |
| Wilkes-Barre/Scranton Intl Airport, PA | isd | 0.98 | -0.82 | Lehigh Valley International Airport 71 km, Williamsport Regional Airport 98 km, Rdng Rgnl/C A Spaatz Fd Ap 99 km |
| Trenton Mercer Airport, NJ | isd-linked | 0.98 | +0.69 | Mcguire Afb Airport 29 km, Ne Philadelphia Airport 29 km, South Jersey Regional Arpt 35 km, Philadelphia International Airport 58 km |
| Parkersburg/Mid-Ohio Valley Regional Airport, WV | isd | 0.98 | -0.00 | no land station within 100 km |
| Wheeling Ohio County Arpt, WV | isd-linked | 0.99 | +0.82 | Pittsburgh International Airport 52 km, Allegheny County Airport 71 km, Akron-Canton Regional Airport 95 km, Mgtn Rgnl-W L B Hart Fd Ap 97 km |
| Pittsburgh International Airport, PA | isd | 0.99 | +0.12 | Allegheny County Airport 32 km, Wheeling Ohio County Arpt 50 km, Youngstown-Warren Regional Airport 91 km, Mgtn Rgnl-W L B Hart Fd Ap 99 km |
| Allegheny County Airport, PA | isd | 0.99 | +0.06 | Pittsburgh International Airport 32 km, Wheeling Ohio County Arpt 55 km, Mgtn Rgnl-W L B Hart Fd Ap 67 km, J Murtha Jtwn-Cmbra Co Apt 99 km |
| Williamsport Regional Airport, PA | isd | 0.99 | -1.45 | no land station within 100 km |
| Dutchess County Airport, NY | isd-linked | 0.99 | +0.10 | no land station within 100 km |
| Akron-Canton Regional Airport, OH | isd | 0.99 | -0.48 | Youngstown-Warren Regional Airport 75 km |
| Washington Dulles International Ap, VA | isd | 0.99 | -0.04 | Ronald Reagan Washington Natl Ap 44 km, Etrn Wv Rgnl/Shpherd Fd Ap 61 km, Baltimore-Washington Intl Airport 73 km, Hgrtwn Rgnl-R.Hnson Fld Ap 81 km |
| Elmira/Corning Rgnl Arpt, NY | isd-linked | 0.99 | -1.75 | Ithaca Tompkins Regional Airport 51 km, Greater Binghamton/E A Link Field Ap 84 km |
| Harrisburg International Airport, PA | isd-linked | 0.99 | -0.06 | Capital City Airport 10 km, York Airport 38 km, Lancaster Airport 41 km, Rdng Rgnl/C A Spaatz Fd Ap 68 km |
| Capital City Airport, PA | isd-linked | 0.99 | -0.81 | Harrisburg International Airport 6 km, York Airport 38 km, Lancaster Airport 41 km, Rdng Rgnl/C A Spaatz Fd Ap 68 km |
| Bradford Regional Airport, PA | isd | 0.99 | +0.43 | Du Bois-Jefferson Co Arpt 65 km |
| Mgtn Rgnl-W L B Hart Fd Ap, WV | isd | 0.99 | -0.12 | Harrison/Marion Rgnl Arpt 53 km, Allegheny County Airport 68 km, Wheeling Ohio County Arpt 72 km, Pittsburgh International Airport 84 km |
| Youngstown-Warren Regional Airport, OH | isd | 0.99 | +0.91 | Akron-Canton Regional Airport 69 km, Pittsburgh International Airport 96 km |
| York Airport, PA | isd-linked | 0.99 | +0.22 | Capital City Airport 27 km, Harrisburg International Airport 29 km, Lancaster Airport 62 km, Hgrtwn Rgnl-R.Hnson Fld Ap 70 km |
| Rdng Rgnl/C A Spaatz Fd Ap, PA | isd-linked | 0.99 | -0.98 | Lancaster Airport 29 km, Lehigh Valley International Airport 64 km, Harrisburg International Airport 66 km, Wilmington Airport 72 km |
| Greater Binghamton/E A Link Field Ap, NY | isd | 0.99 | +1.44 | Ithaca Tompkins Regional Airport 46 km, Elmira/Corning Rgnl Arpt 75 km |
| Lehigh Valley International Airport, PA | isd | 1.00 | -0.16 | Rdng Rgnl/C A Spaatz Fd Ap 57 km, Wilkes-Barre/Scranton Intl Airport 68 km, Trenton Mercer Airport 78 km, Ne Philadelphia Airport 85 km |
| Etrn Wv Rgnl/Shpherd Fd Ap, WV | isd | 1.00 | -0.07 | Hgrtwn Rgnl-R.Hnson Fld Ap 33 km, Washington Dulles International Ap 79 km, Altoona-Blair County Arpt 93 km |
| Harrison/Marion Rgnl Arpt, WV | isd-linked | 1.00 | -0.11 | Elkins-Rand Co-J.Rand Field Airport 53 km, Mgtn Rgnl-W L B Hart Fd Ap 53 km |
| J Murtha Jtwn-Cmbra Co Apt, PA | isd-linked | 1.00 | +1.68 | Altoona-Blair County Arpt 37 km, Allegheny County Airport 100 km |
| Du Bois-Jefferson Co Arpt, PA | isd-linked | 1.00 | +0.44 | Bradford Regional Airport 68 km |
| Elkins-Rand Co-J.Rand Field Airport, WV | isd | 1.00 | -1.37 | Harrison/Marion Rgnl Arpt 53 km, Mgtn Rgnl-W L B Hart Fd Ap 74 km |
| Hgrtwn Rgnl-R.Hnson Fld Ap, MD | isd-linked | 1.00 | -0.28 | Etrn Wv Rgnl/Shpherd Fd Ap 43 km, York Airport 77 km, Altoona-Blair County Arpt 78 km, Capital City Airport 92 km |

## Places through the cooling model

The place's cell against the station's own record, p50 per 100 MW, % difference.

| Place | Station (km) | Cell land | towers avg | towers peak | hybrid avg | hybrid peak | assist avg | assist peak |
|---|---|---|---|---|---|---|---|---|
| Highspire borough | Harrisburg International Airport (2) | 0.99 | -0 | -1 | -4 | -8 | -1 | -9 |
| Tinicum township | Philadelphia International Airport (2) | 0.94 | -1 | -0 | -11 | -3 | -15 | -6 |
| Rockledge borough | Ne Philadelphia Airport (6) | 0.96 | -0 | -0 | -12 | -4 | -16 | -6 |
| Muhlenberg township | Rdng Rgnl/C A Spaatz Fd Ap (4) | 1.00 | -1 | -2 | -11 | -4 | -20 | -11 |
| Jackson township | York Airport (1) | 0.97 | +0 | +2 | +4 | +8 | +4 | +8 |
| Manheim township | Lancaster Airport (3) | 0.97 | -0 | +1 | +0 | +5 | +1 | +7 |
| New Cumberland borough | Capital City Airport (2) | 0.97 | -1 | -1 | -13 | -2 | -23 | -7 |
| Washington township | Du Bois-Jefferson Co Arpt (3) | 1.00 | -1 | +1 | -6 | +5 | -3 | +10 |
| Martinsburg borough | Altoona-Blair County Arpt (1) | 0.97 | +1 | -0 | +10 | -1 | +10 | +3 |
| Richland township | J Murtha Jtwn-Cmbra Co Apt (3) | 1.00 | +1 | +2 | +22 | +2 | +21 | +15 |
| Avoca borough | Wilkes-Barre/Scranton Intl Airport (2) | 0.98 | -1 | -1 | -17 | -6 | -29 | -8 |
| Montoursville borough | Williamsport Regional Airport (0) | 0.99 | -1 | -1 | -11 | -1 | -20 | +1 |

A fail is a method question for Andrew; the command changes nothing. Criteria: `waterledger.national.era5_check.CRITERIA`.
