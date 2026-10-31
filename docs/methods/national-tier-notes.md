# Methods notes: from Michigan to the national tier

A running record of how each part of Water Ledger Michigan's method maps to the national tier: the sources, the decisions,
and where a state's numbers differ from Michigan's and why. It is the raw material for two products:

1. a short methods brief for each state (PDF, in `docs/methods/<st>.pdf`);
2. a methods page for each state on waterledger.org (`/<st>/methods`), like Michigan's.

Test states: Ohio, Virginia and Texas (design 0002). Dates are when the decision was made.

## Places (Oct 29, 2026)

| | Michigan | National tier |
|---|---|---|
| Source | Census TIGERweb county subdivisions | Census TIGERweb incorporated places, county subdivisions and counties |
| Units | Cities and townships (1,541); villages take their township's water facts | Cities, towns and villages everywhere; townships only where the Census marks them as active governments (FUNCSTAT A, about 20 states); every county, for unincorporated land |
| Skipped | Census "fictitious" subdivisions that repeat a city; water-only areas | Also statistical subdivisions (Texas census county divisions) and nonfunctioning ones (Virginia magisterial districts); independent cities listed once, as cities |
| Point lookup | The county subdivision containing the point | The most local government containing the point: city, town or village, else township, else county |

Counts: Ohio 2,318 places (1,308 townships, 922 cities and villages, 88 counties); Virginia 322 (227 cities and towns, 95
counties); Texas 1,481. Census-designated places (Ashburn, Virginia) are not governments and resolve to their county.

## Water supply (Oct 29, 2026)

- Source, both tiers: EPA Community Water System Service Area Boundaries, with SDWIS population served and connections.
- Join:
  - Michigan: the share of each place a system covers, from a sample grid.
  - National tier: the share by area, in an equal-area projection (EPSG:5070).
  - National tier only: systems covering under 0.5% of a place are left out, and reprojected boundaries are repaired
    (make_valid).
- With no system mapped in a place: the nearest system serving more than 3,300 people (EPA's medium size and up).
  - Michigan: measured center to center.
  - National tier: measured edge to edge.
- County water use (Oct 30, 2026; `waterledger_data.wateruse`, details in [water-use-sources.md](water-use-sources.md)):
  - Michigan: EGLE's reported withdrawals by sector (2025).
  - National tier: USGS's revised 2015 county estimates for every state (labeled estimates), replaced by a state's own
    figures where Water Ledger reads them: Ohio ODNR registration (reported withdrawals, 2024), Texas TWDB Water Use
    Survey (TWDB's "use", 2024), Virginia DEQ locality totals (reported withdrawals excluding power, 2024).
  - The estimate and impacts don't depend on it (design 0002, decision 6).

Checks: Columbus 98% Columbus Public Water; Richmond 99.8% its own system; Austin 67% Austin Water; Loudoun County 26%
Loudoun Water (most of the county is on wells).

## Wastewater (Oct 29, 2026)

- Source, both tiers: EPA Clean Watersheds Needs Survey 2022 (design flow, location), matched by NPDES permit to EPA ECHO
  (last-year average flow, receiving water, major/minor, combined sewer).
- Which plants count:
  - Michigan: also keeps survey plants without an ECHO match (state-permitted groundwater dischargers, lagoons).
  - National tier: only plants with an active, unexpired NPDES permit in ECHO. This leaves out capital-project and
    collection-system records and closed plants still in the survey (Austin's Govalle, closed 2009).
- A design flow of 0 is treated as unknown.
- ECHO flows outside 10-130% of design are dropped (unit errors).
- Order of nearby plants (within 40 km):
  - Michigan: the place's own plant (same city) first, then by distance.
  - National tier: by distance only, with a same-city flag, because the survey's city is the mailing city (Austin's South
    Austin Regional plant is listed in Del Valle).

Counts: Ohio 669 plants, Virginia 217, Texas 1,059.

## Receiving waters (Oct 29, 2026)

- Watersheds, both tiers: USGS Watershed Boundary Dataset HUC12 and HUC8.
  - Michigan: from a sample grid.
  - National tier: area shares in the equal-area projection, keeping watersheds that cover at least 1% of a place.
- Impairments:
  - Michigan: EPA ATTAINS, with the HUC12 read from Michigan's assessment unit IDs (a Michigan convention).
  - National tier: EPA's own assessment-unit-to-HUC12 crosswalk (ATTAINS "Assessments by HUC12"), so no state
    convention is needed.
- Causes are grouped into the same plain-language groups as Michigan. A cause has a TMDL when its category is 4A.
- Downstream path:
  - National tier: the watershed tracer (`waterledger_data.trace`, formerly attains-trace), following each HUC12's
    downstream neighbor to the outlet, across state lines. Context shows the first 25 HUC12s, as Michigan does.
  - Columbus runs down the Scioto, Ohio and Mississippi; Loudoun down the Potomac to the Atlantic; Austin down the
    Colorado to the Gulf of Mexico.
- Michigan only: coldwater (DNR trout) streams. Other states' equivalents come as state layers.
- ATTAINS reporting cycles differ by state (Ohio 2024, Virginia 2024, Texas 2026, Michigan 2026).

## Climate (Oct 29, 2026)

- Weather:
  - Michigan: ERA5 reanalysis (Open-Meteo) at eight hand-picked regions, 1995-2024.
  - National tier: NOAA ISD station observations, one station per NOAA climate division: the station with at least 85%
    of hours observed over 1995-2024 nearest the center of the division's counties.
  - Gaps of up to 6 hours are filled linearly, longer ones with the station's mean for that month and hour. Relative
    humidity comes from dew point (Magnus).
- The weather source matters for the hot-hour designs. In Michigan, station records give:
  - cooling towers within 1% of ERA5;
  - hybrid and evaporative assist 4-50% higher in the south and 2-5 times higher at Traverse City and Alpena;
  - peak days mostly within 20%.

  Michigan stays on ERA5 until a reviewed model change (design 0001, decision 5), so national and Michigan hybrid
  numbers are not strictly comparable. Every methods page must say this.
- Stations chosen:
  - Ohio, all 10 divisions: Findlay (2), Cleveland, Dayton, Port Columbus, Akron-Canton (2), Cincinnati Lunken, Huntington
    Tri-State, Zanesville.
  - Virginia, all 6: Richmond (2), Lynchburg, Dulles, Roanoke, and Beckley, West Virginia (99 km) for the southwest.
  - Texas, all 10: Lubbock, Abilene, Fort Worth NAS, Lufkin, Winkler County, Junction, Victoria, Houston
    Intercontinental, Cotulla, McAllen.
  - 87-100% of hours observed.
  - Compromises to revisit:
    - Some divisions share a station.
    - Austin's division (South Central) is represented by Victoria, near the division's center but more humid than
      Austin.
    - Later: the station nearest each place.
- The cooling Monte Carlo (200 runs, the same parameters and seeds as Michigan) runs on each division's station record.
- Design storms, both tiers: NOAA Atlas 14 24-hour depths at each county's internal point. Older NOAA studies will fill
  states outside Atlas 14 when needed; Ohio, Virginia and Texas are all covered (Texas: Volume 11, 2018).
- Rainfall: NOAA Climate at a Glance means, 1991-2020, by county and independent city. A city NOAA has no record for takes its surrounding county's (Lexington, Virginia: Rockbridge County, 44.79 inches); a county with none stops the build.

300 MW, cooling towers, average withdrawal (million gallons a day): Gaines (Michigan, ERA5) 2.34; Columbus 2.40;
Loudoun County 2.43; Austin 2.66.

## Energy (Oct 29, 2026)

- Utility territories:
  - Michigan: MPSC.
  - National tier: the HIFLD Electric Retail Service Territories layer (Oak Ridge National Laboratory). HIFLD Open shut
    down on Aug 26, 2025; the live copy used is PNNL's
    (eedgis.pnnl.gov, Hosted/Electric_Service_Territories).
  - Some HIFLD territories are drawn from county boundaries where better geometry wasn't available.
- Utility sales, customers and peaks: EIA-861, by state (Michigan's method, generalized). HIFLD's own figures are from 2020.
- Water at the power plants:
  - Michigan's choices: its own fleet mix, coal, nuclear, gas, renewables, and the MISO average.
  - National tier: the utility's balancing authority (HIFLD control area), with the 2022 consumption intensity from
    Siddik et al. (2024, LBNL Water IMPACT), weighted by electricity use, excluding hydropower reservoir evaporation, as
    Michigan's MISO figure does.
  - MISO 1.570 L/kWh (Michigan's published figure), PJM 1.298, ERCOT 0.730, SPP 0.940, TVA 0.955, Southern 1.517.

- Order of a place's utilities: by EIA customers in the state. Area shares are kept but shown as "may serve": HIFLD draws
  many small utilities as whole counties, so Westerville's municipal utility "covers" 99% of Columbus. Ranking by
  customers gives AEP Ohio for Columbus, Dominion (Virginia Electric & Power) for Loudoun County and Austin Energy for
  Austin. Michigan uses MPSC territories, which are drawn to actual boundaries, and keeps its shares.
- Every place in Ohio and Texas, and 315 of 322 in Virginia, has at least one territory.

## Trackers (Oct 29, 2026)

Proposal and moratorium trackers are a waterledger.org feature, not part of the packages. The working files (Michigan's
moratoria spreadsheet and proposals list, each entry with its sources and verification date) stay private in the
Northline repo, and the information is public on the site. The packages answer what a facility would mean for water at
a place; they don't carry tracker data, and Context's jurisdiction category does not list moratoria or proposals. The
moratoria builder now in `waterledger.states.mi` moves to Northline.

## Still to decide or build

- Per-state rules files (federal only at first; "state rules not yet reviewed").
- The station nearest each place instead of one per division.
- Reconciling Michigan's ERA5 with station records (a future model version).
- Snapshot releases and the local fallback (design 0003).
