# Weather station distance and the cooling estimates

Working note (Oct 29, 2026), for the methods appendix. Nothing in the models, parameters or published snapshots was
changed for this check.

## Question

The national tier gives every place in a NOAA climate division the weather of one NOAA ISD station: the station with at
least 85% of hours observed over 1995-2024 nearest the center of the division's counties
(`waterledger_data.divisions.division_stations`). Austin, Texas, is in the South Central division and gets Victoria
Regional Airport, 179 km away and nearer the coast. How far are places from their weather, and how much would the
cooling water estimates change with a nearer station that meets the same rule?

## Method

**Distances.** For Ohio, Virginia and Texas, from the 2026-10-30 snapshots: great-circle distance from each place's
Census internal point to its division's station. For Michigan, the same to the ERA5 point of the place's region (eight
hand-picked points, `waterledger.states.mi.build.REGIONS`). Population weights use the 2020 Census centers of population
by tract (U.S. Census Bureau 2021), each tract assigned to its county's division (Michigan: the nearest region point,
as the Michigan build assigns places). Poquoson, Virginia, which NOAA's county table leaves out, takes the nearest
division's station, as the build does.

**Nearer station.** For a sample of 19 places, the nearest ISD station meeting the snapshot rule, searched from the
place's own point: a U.S. station with a WBAN number whose ISD record spans 1995-2024 under one station ID
(`waterledger_data.climate.isd_stations`), and at least 85% of hours with temperature and dew point observed
(`isd_hourly`, same gap filling). The sample covers the places named in the request (Austin, Houston, El Paso, Lubbock,
Dallas, Loudoun County, Richmond, Roanoke, Cincinnati, Cleveland, Columbus) and others where the division station is far
or in a different setting (San Antonio, Round Rock, Amarillo, Virginia Beach, Bristol, Lorain, Toledo, and three
Michigan places).

**Cooling runs.** `waterledger_models.datacenter.cooling.run_location` on each station's hourly record, 1995-2024,
200 Monte Carlo runs, seed 7, per 100 MW of IT capacity, model 1.2: the same call the snapshot builds make
(`waterledger.national.climate.division_runs`). The runs on the division stations reproduce the published snapshot
values exactly (checked for every design and both statistics below), and the runs on Michigan's ERA5 points reproduce
the Michigan snapshot to its five published decimals. Results are the p50 of cooling withdrawal (makeup water) per
100 MW: the average day, and the 1-in-10 peak day (90th percentile of the 30 annual maximum days). Staff water does not
depend on weather and is left out, so the percentages below are larger than they would be for a whole campus.

Difference = (published - nearer) / nearer. Positive means the published estimate is higher than the nearer station's.

**Michigan.** Michigan's weather is ERA5 reanalysis (Open-Meteo archive), not station records, so each Michigan place
gets two comparisons: ERA5 at its region point against ERA5 at the place itself (distance only, same source), and ERA5 at
the region point against the nearest qualifying ISD station (distance and source together).

## Results

### Distance to the weather point

| State | Weather points | Places | Median km | 90th pct km | Max km | Places >50 km | Places >100 km | People >50 km | People >100 km | People >150 km |
|---|---|---|---|---|---|---|---|---|---|---|
| Ohio | 10 stations (8 distinct) | 2,318 | 58 | 96 | 151 | 60% | 7% | 39% | 6% | 0% |
| Virginia | 6 stations (5 distinct) | 322 | 86 | 147 | 215 | 80% | 35% | 49% | 25% | 3% |
| Texas | 10 stations | 1,481 | 115 | 209 | 354 | 85% | 58% | 66% | 42% | 27% |
| Michigan | 8 ERA5 points | 1,541 | 59 | 108 | 216 | 60% | 15% | 39% | 4% | 1% |

Population-weighted median distance: Ohio 39 km, Virginia 43 km, Texas 76 km, Michigan 41 km (90th percentile 88, 128,
189 and 77 km).

Farthest places:

- Texas: Mobeetie (Wheeler County), 354 km from Abilene; Follett (Lipscomb County), 344 km from Lubbock; El Paso's
  places, up to 322 km from Winkler County Airport. Round Rock is in the North Central division and gets Fort Worth NAS,
  250 km away.
- Virginia: Lee County, 215 km from Beckley, West Virginia; Scott County towns 181-190 km.
- Ohio: Lorain County places, 140-151 km from Findlay (division 2).
- Michigan: Whitefish Township (Chippewa County), 216 km from the Alpena point; Ironwood, 211 km from the Marquette point.

Texas is the outlier: 42% of Texans live more than 100 km from their weather station, against 4-25% elsewhere.

### Nearest qualifying station

| Place | Division station (km) | Nearest qualifying station (km) | Skipped (share of hours observed) |
|---|---|---|---|
| Austin | Victoria (179) | San Antonio Intl (110) | Robert Gray AAF (82%), Hood AAF (68%), Randolph AFB (79%) |
| San Antonio | Victoria (168) | San Antonio Intl (10) | |
| Round Rock | Fort Worth NAS (250) | Waco (128) | same three as Austin |
| Dallas | Fort Worth NAS (64) | DFW Intl (26) | Dallas Love Field (48%) |
| El Paso | Winkler County (305) | El Paso Intl (6) | |
| Amarillo | Lubbock (171) | Amarillo (10) | |
| Virginia Beach | Richmond (141) | Oceana NAS (4) | |
| Bristol | Beckley, WV (159) | Asheville, NC (136) | |
| Lorain | Findlay (133) | Cleveland Hopkins (28) | |
| Toledo | Findlay (73) | Toledo Express (20) | |
| Port Huron, MI | ERA5 southeast point (126) | Detroit City Airport (80) | Selfridge ANGB (82%) |
| Ironwood, MI | ERA5 UP point (211) | Houghton County (150) | |
| Gaines Twp, MI | ERA5 west point (11) | Grand Rapids Ford Intl (11) | |

For Houston (Bush Intercontinental, 22 km), Lubbock, Loudoun County (Dulles), Richmond, Roanoke, Cincinnati (Lunken),
Cleveland (Hopkins) and Columbus (Port Columbus), the division station is already the nearest qualifying station, so
their estimates would not change.

Austin's own stations do not qualify. In ISD, Austin Mueller (722540-13958) ends in 1997, and Camp Mabry
(722544-13958) and Austin-Bergstrom (722540-13904) start in 1999, so none spans 1995-2024 under one ID. Tri-Cities
(Bristol) has the same problem: 723181-13877 ends in 1990, 723350-13877 starts in 2005. Austin's comparison was
therefore repeated on a common 2000-2024 period with Camp Mabry (3 km from Austin's internal point) and Bergstrom
(15 km).

### Cooling withdrawal, average day, MGD per 100 MW (p50)

| Place | Published point | Nearer point | Towers pub / near | Diff | Hybrid pub / near | Diff | Assist pub / near | Diff |
|---|---|---|---|---|---|---|---|---|
| Austin, San Antonio | Victoria | San Antonio Intl | 0.887 / 0.880 | +1% | 0.212 / 0.221 | -4% | 0.0217 / 0.0244 | -11% |
| Austin, 2000-2024 | Victoria | Camp Mabry | 0.888 / 0.878 | +1% | 0.216 / 0.228 | -5% | 0.0223 / 0.0272 | -18% |
| Austin, 2000-2024 | Victoria | Austin-Bergstrom | 0.888 / 0.875 | +2% | 0.216 / 0.214 | +1% | 0.0223 / 0.0254 | -12% |
| Round Rock | Fort Worth NAS | Waco | 0.865 / 0.867 | 0% | 0.230 / 0.214 | +8% | 0.0290 / 0.0263 | +10% |
| Dallas | Fort Worth NAS | DFW Intl | 0.865 / 0.864 | 0% | 0.230 / 0.222 | +4% | 0.0290 / 0.0264 | +10% |
| El Paso | Winkler County | El Paso Intl | 0.848 / 0.838 | +1% | 0.223 / 0.208 | +7% | 0.0316 / 0.0259 | +22% |
| Amarillo | Lubbock | Amarillo | 0.826 / 0.810 | +2% | 0.150 / 0.119 | +26% | 0.0178 / 0.0138 | +29% |
| Virginia Beach | Richmond | Oceana NAS | 0.825 / 0.832 | -1% | 0.097 / 0.092 | +5% | 0.0080 / 0.0060 | +33% |
| Bristol | Beckley | Asheville | 0.789 / 0.807 | -2% | 0.021 / 0.040 | -48% | 0.0004 / 0.0014 | -75% |
| Lorain | Findlay | Cleveland Hopkins | 0.790 / 0.790 | 0% | 0.053 / 0.043 | +22% | 0.0030 / 0.0021 | +41% |
| Toledo | Findlay | Toledo Express | 0.790 / 0.787 | 0% | 0.053 / 0.051 | +3% | 0.0030 / 0.0032 | -5% |
| Port Huron | ERA5 southeast | ERA5 at Port Huron | 0.781 / 0.778 | 0% | 0.035 / 0.026 | +31% | 0.0015 / 0.0010 | +54% |
| Port Huron | ERA5 southeast | Detroit City (ISD) | 0.781 / 0.787 | -1% | 0.035 / 0.049 | -29% | 0.0015 / 0.0026 | -42% |
| Ironwood | ERA5 UP | ERA5 at Ironwood | 0.755 / 0.749 | +1% | 0.012 / 0.013 | -4% | 0.0004 / 0.0004 | +9% |
| Ironwood | ERA5 UP | Houghton County (ISD) | 0.755 / 0.746 | +1% | 0.012 / 0.011 | +8% | 0.0004 / 0.0004 | +13% |
| Gaines Twp | ERA5 west | ERA5 at Gaines | 0.778 / 0.778 | 0% | 0.031 / 0.030 | +5% | 0.0012 / 0.0011 | +9% |
| Gaines Twp | ERA5 west | Grand Rapids (ISD) | 0.778 / 0.779 | 0% | 0.031 / 0.039 | -19% | 0.0012 / 0.0019 | -36% |

### Cooling withdrawal, 1-in-10 peak day, MGD per 100 MW (p50)

| Place | Published point | Nearer point | Towers pub / near | Diff | Hybrid pub / near | Diff | Assist pub / near | Diff |
|---|---|---|---|---|---|---|---|---|
| Austin, San Antonio | Victoria | San Antonio Intl | 1.014 / 1.030 | -2% | 0.784 / 0.914 | -14% | 0.123 / 0.158 | -22% |
| Austin, 2000-2024 | Victoria | Camp Mabry | 1.015 / 1.037 | -2% | 0.794 / 0.913 | -13% | 0.125 / 0.158 | -21% |
| Austin, 2000-2024 | Victoria | Austin-Bergstrom | 1.015 / 1.026 | -1% | 0.794 / 0.846 | -6% | 0.125 / 0.145 | -14% |
| Round Rock | Fort Worth NAS | Waco | 1.051 / 1.036 | +1% | 1.006 / 0.926 | +9% | 0.189 / 0.162 | +17% |
| Dallas | Fort Worth NAS | DFW Intl | 1.051 / 1.048 | 0% | 1.006 / 1.007 | 0% | 0.189 / 0.183 | +3% |
| El Paso | Winkler County | El Paso Intl | 1.034 / 1.035 | 0% | 0.897 / 0.981 | -9% | 0.157 / 0.184 | -15% |
| Amarillo | Lubbock | Amarillo | 1.027 / 1.010 | +2% | 0.883 / 0.756 | +17% | 0.150 / 0.129 | +17% |
| Virginia Beach | Richmond | Oceana NAS | 1.014 / 1.014 | 0% | 0.785 / 0.830 | -5% | 0.129 / 0.135 | -4% |
| Bristol | Beckley | Asheville | 0.950 / 0.959 | -1% | 0.393 / 0.438 | -10% | 0.044 / 0.057 | -22% |
| Lorain | Findlay | Cleveland Hopkins | 0.990 / 0.985 | +1% | 0.676 / 0.655 | +3% | 0.104 / 0.103 | +1% |
| Toledo | Findlay | Toledo Express | 0.990 / 0.992 | 0% | 0.676 / 0.693 | -3% | 0.104 / 0.116 | -10% |
| Port Huron | ERA5 southeast | ERA5 at Port Huron | 0.984 / 0.988 | 0% | 0.636 / 0.656 | -3% | 0.090 / 0.092 | -2% |
| Port Huron | ERA5 southeast | Detroit City (ISD) | 0.984 / 1.003 | -2% | 0.636 / 0.735 | -14% | 0.090 / 0.120 | -25% |
| Ironwood | ERA5 UP | ERA5 at Ironwood | 0.972 / 0.969 | 0% | 0.519 / 0.516 | +1% | 0.078 / 0.074 | +6% |
| Ironwood | ERA5 UP | Houghton County (ISD) | 0.972 / 0.964 | +1% | 0.519 / 0.512 | +1% | 0.078 / 0.076 | +4% |
| Gaines Twp | ERA5 west | ERA5 at Gaines | 0.980 / 0.978 | 0% | 0.646 / 0.627 | +3% | 0.083 / 0.081 | +3% |
| Gaines Twp | ERA5 west | Grand Rapids (ISD) | 0.980 / 0.988 | -1% | 0.646 / 0.683 | -5% | 0.083 / 0.095 | -12% |

The dry design (loop top-ups only) does not use weather and is identical at every point (0.00003 MGD per 100 MW).

## Interpretation

**Cooling towers are insensitive.** Every comparison is within 2% for both the average and the peak day. Towers
evaporate all year, and the evaporative ratio changes slowly with dry-bulb temperature, so a 100-300 km shift in
weather moves the annual total very little. At 300 MW, Victoria gives 2.66 MGD of tower cooling withdrawal on an
average day; Austin's own stations give 2.63-2.64 MGD (2000-2024).

**Hybrid and evaporative assist are sensitive.** These designs evaporate only above a dry-bulb setpoint, so their water
depends on how many hours cross the setpoint and by how much. Across the sample, the published hybrid average is -48% to
+26% of the nearer station's, assist -75% to +41%, hybrid peak days -14% to +17%, assist peak days -22% to +17%. In
absolute terms the assist average is small (0.0004-0.03 MGD per 100 MW), so its large percentages are a small number of
gallons; the hybrid differences are larger in gallons (Amarillo: 0.031 MGD per 100 MW, about 93,000 gallons a day at
300 MW; peak day 0.13 MGD per 100 MW).

**The direction is not consistent.** Victoria, near the coast, understates Austin's and San Antonio's peak days (hybrid
-6 to -14%, assist -14 to -22%) but gets Austin's tower and hybrid averages within 5%. Lubbock overstates Amarillo by 17-29%
(Amarillo is higher and cooler). Findlay overstates Lorain's averages (lake-moderated) but understates Toledo's assist
peak. So the single-station design is not biased one way; it adds scatter.

**Distance alone is a poor predictor.** Ironwood is 211 km from the Marquette point and changes by less than 10%; Dallas
is 64 km from Fort Worth NAS and its assist average changes by 10%; Bristol and its replacement (Asheville) are both
mountain stations in different basins and differ by half for the hybrid average. Elevation, lake and coast exposure, and
latitude matter more than kilometers.

**Most differences sit inside the parameter range.** The published p10-p90 band for the hybrid average is wide (Austin
0.156-0.289 MGD per 100 MW; Amarillo 0.115-0.194; Lorain 0.032-0.078). Every nearer-station p50 in the sample falls
inside the published hybrid-average band except Bristol, where Asheville's p50 (0.040) is at the published p90 (0.039). The station
choice is a smaller source of uncertainty than the design parameters (setpoints, cycles, utilization) for the average
day, and comparable to it for the 1-in-10 peak day of hybrid and assist designs.

**The weather source matters as much as the distance.** At Gaines Township, Grand Rapids airport records give a hybrid
average 23% higher than the ERA5 point 11 km away (which is within 5% of ERA5 at Gaines itself), and an assist average
56% higher, with towers within 1%. This
matches the earlier Michigan comparison recorded in `national-tier-notes.md` (towers within 1%, hybrid and assist 4-50%
higher on station records in southern Michigan, 2-5 times at Traverse City and Alpena). That earlier comparison was run
ad hoc on Oct 29, 2026 against ten Michigan ISD airports (Detroit Metro, Willow Run, Lansing, Kalamazoo, Grand Rapids,
Saginaw MBS, Traverse City, Alpena, Marquette, Houghton; ISD-Lite files cached in Northline's `engine/data/raw/isd/`);
its script and result tables were not committed, only the summary. At Port Huron, the two effects cancel in part: the
southeast ERA5 point overstates Port Huron's ERA5 hybrid average by 31% (Port Huron is lake-cooled), while station
records run higher than ERA5.

## Options

Costs are estimates from this check: ISD-Lite averages 82 KB per station-year (2.5 MB per 30-year record); one cooling
run (200 Monte Carlo runs, four designs, 30 years) took 13-21 s on one core of a laptop; an Open-Meteo ERA5 30-year
hourly point is 6.7 MB of JSON; each weather point adds about 8.7 KB to a snapshot's `climate.json` (unrounded; Michigan's
rounded entries are 5.6 KB). Current snapshots are 4.7 MB (Ohio), 1.5 MB (Virginia) and 6.0 MB (Texas).

**A. Nearest qualifying station per place.** Each place gets the nearest station meeting the 85% rule; the snapshot stores
one run per station used and a station ID and distance per place. Before the coverage check, the nearest candidate
station for every place comes to 21 distinct stations in Ohio, 25 in Virginia and 53 in Texas (40, 38 and 60
candidates within 150 km), and the median place would be 40-51 km from its station (90th percentile 66-100 km; maximum
91-168 km). Estimated cost: downloads up to 100 MB (Ohio), 95 MB (Virginia), 150 MB (Texas), counting stations that
fail the coverage check; build 5-20 minutes of cooling runs per state; snapshot +0.1 to +0.4 MB. It removes the worst
cases (El Paso, Amarillo, Lorain, Virginia Beach) and keeps every number traceable to one named station.

**B. Several stations per division, interpolated.** Each place gets an inverse-distance-weighted combination of the
results of its two or three nearest qualifying stations. Same downloads and runs as A; snapshot +0.1 to +0.4 MB plus a
few IDs and weights per place (about 90 KB for Texas). It removes jumps at division lines, but weighting percentiles is an
approximation (a weighted p50 is not the p50 of a mixed climate), it blends across coasts and ridges (Bristol), and the
estimate no longer names one station.

**C. ERA5 everywhere, as in Michigan.** One ERA5 point per 0.25-degree cell that holds a place (or per county). Upper
bounds by area: about 1,050 cells in Texas, 200 in Ohio and 180 in Virginia [estimate]; 6.7 MB each as Open-Meteo JSON
(Texas about 7 GB), build about 4.4 hours for Texas and under an hour for Ohio or Virginia, snapshot +9 MB for Texas
(+1.7 and +1.6 MB). Per county instead: 254, 88 and 133 points (Texas 1.7 GB, about 1 hour, +2.2 MB). Michigan's eight
30-year points were fetched from Open-Meteo on three separate days (Oct 20, 25 and 26); a national ERA5 build would need
bulk access to ERA5 (Copernicus Climate Data Store, or a cloud copy) rather than the free point API [estimate]. This is a
model change, not a resolution fix: in Michigan, station records give hybrid and assist estimates 4-56% higher than
ERA5 at the same place in the south and 2-5 times higher in the north, as large as or larger than the distance effects
measured here.

**D. Link station records across ID changes.** Treat ISD records that share a WBAN number as one station when checking
the 1995-2024 span and the 85% rule. Austin's Camp Mabry and Bergstrom records start in 1999 under new USAF IDs, and
Tri-Cities (Bristol) changed IDs with a gap; under the current rule all are skipped. This costs nothing in snapshot size
and a few station downloads. It is needed for A or B to reach Austin's own stations; whether the 1995-1999 gap at
Austin can be closed from the older ID was not checked.

## Recommendation

A with D: the nearest qualifying station per place, with ISD records linked by WBAN, and the station's name and
distance stored with each place so the page can show them. It is cheap (well under 1 MB per snapshot and minutes of
build time), fixes the cases where a place is hundreds of kilometers from its station or in a different setting, and
keeps each estimate traceable to a named record. Add a flag when the nearest qualifying station is more than about 100
km away or differs from the place by more than a few hundred meters in elevation, rather than silently using it.

Do not move the national tier to ERA5 on the strength of this check. Station distance and weather source change the
hybrid and assist results by similar amounts, and the open question is which source is right for hot-hour designs.
That belongs with the planned reconciliation of Michigan's ERA5 and the national tier's station records, as a reviewed
model change. Towers and dry designs do not need either change.

## Limits

- 19 places, chosen where the station was expected to matter; the ranges above are not a statewide distribution. A
  statewide pass under option A would give one.
- Airport stations stand for the place's internal point, not a campus site. Urban heat, lake breezes and valley
  effects at a real site are not represented by either station.
- Distances are from the Census internal point of each place. Large counties (unincorporated land) can be far from
  that point in every direction.
- Gap filling (linear to 6 hours, then the station's month-hour mean) and the 85% rule are as published; stations near
  the threshold carry more filled hours. Times are local standard time from longitude.
- The p50 of a 200-run Monte Carlo with a fixed seed. Station-to-station differences are single comparisons; no
  sampling error for them was estimated.
- Assist averages are a few thousandths of an MGD per 100 MW, so their percentage differences are unstable.
- Austin's comparison with its own stations covers 2000-2024, not 1995-2024; Victoria's numbers on the two periods
  differ by under 3%.
- The cost figures for options A-C are estimates from timings and file sizes on one machine.

## Data

- NOAA National Centers for Environmental Information. Integrated Surface Database (ISD) and ISD-Lite, hourly
  temperature and dew point, 1995-2024; station history file `isd-history.csv`.
  https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database. Smith, A., Lott, N. and Vose, R.
  (2011). The Integrated Surface Database: recent developments and partnerships. Bulletin of the American
  Meteorological Society 92(6): 704-708.
- NOAA NCEI climate divisions, county-to-division table (`county-to-climdivs.txt`). Vose, R. S., et al. (2014). Improved
  historical temperature and precipitation time series for U.S. climate divisions. Journal of Applied Meteorology and
  Climatology 53(5): 1232-1251.
- U.S. Census Bureau (2021). 2020 Census centers of population by census tract (`CenPop2020_Mean_TR<state>.txt`).
- Hersbach, H., et al. (2020). The ERA5 global reanalysis. Quarterly Journal of the Royal Meteorological Society
  146(730): 1999-2049; accessed through the Open-Meteo historical weather API.
- Water Ledger snapshots for Ohio, Virginia, Texas and Michigan dated 2026-10-30 (model 1.2).
