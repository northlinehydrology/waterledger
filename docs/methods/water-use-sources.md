# Water use by county: sources by state

Working note (Oct 30, 2026). Water Ledger compares a campus's water with the water already used in its county. Michigan
uses EGLE's reported withdrawals. This note records what the national source and the first three national-tier states
publish, so each state can use its own numbers where they exist and the national estimate where they don't.

## Plan

1. **National floor, every state:** USGS county estimates for 2015, revised release (Sleckman, Ross and Cook, 2026,
   doi:10.5066/P14Q6AVK). All categories, golf separable. Labeled as a USGS estimate for 2015, compiled from state
   reports and models; withdrawals in Mgal/d. Not called "reported".
2. **State reports where they exist:** Ohio (ODNR registration), Texas (TWDB Water Use Survey), Virginia (DEQ
   withdrawal reporting), each labeled with its own year, basis and limits.
3. **Show what a county takes and what it delivers.** Withdrawals are counted where water is taken, so counties that buy
   water elsewhere look small (Loudoun withdraws about 7-17 Mgal/d but its homes receive about 27 from public supply).
   Show USGS's public supply delivered to homes (`DO-PSDel`) next to withdrawals.

## National: USGS

| | |
|---|---|
| Release | Revised 2015 county estimates, doi:10.5066/P14Q6AVK (2015 child item `683e0ac3d4be0234870fcafe`, `2015-Revised-County.xlsx` or a parquet zip). Original: Dieter and Linsey 2018, doi:10.5066/F7TB15V5 (CSV, 141 columns) |
| Categories | Public supply, domestic, commercial (revised only), industrial, irrigation (crop, golf), livestock, aquaculture, mining, thermoelectric (once-through, recirculating) |
| Basis | Withdrawals, Mgal/d, fresh and saline, ground and surface; consumptive use only for irrigation and thermoelectric |
| Download | Direct ScienceBase file links |
| Caveats | 2015; no county totals in the revised file (sum Fr + Sa); method codes per county and category |
| Newer | Modeled 2000-2020 public supply, irrigation and thermoelectric by HUC12 or service area (Water Data Companion API), industrial and mining 2020 by county; no single year with every category. Later, as a labeled 2020 update |

Test values (revised 2015, Mgal/d): Kent MI public supply 9.01, total 27.76 (golf 1.91, delivered to homes 31.78);
Franklin OH 155.82 / 188.31; Travis TX 122.10 / 134.11; Loudoun VA 6.86 / 11.62 (11.57 without commercial, 0.05;
delivered to homes 27.08).

## Ohio: ODNR Water Withdrawal Facility Registration

| | |
|---|---|
| Rule | ORC 1521.16: facilities able to withdraw 100,000 gal/day or more register and report every year (Lake Erie and Ohio River basins) |
| Data | Public ArcGIS feature service `services5.arcgis.com/ajRlmtxbNBjZggOT/arcgis/rest/services/Water_Withdrawal_Facility/FeatureServer` (layer 0 facilities; tables 2 surface and 3 groundwater by facility and year, Jan-Dec and total; table 1 return flows), and a weekly file geodatabase (ArcGIS item `3277b6ce52284889a4b39c6ecfb013d1`) |
| Years | 1990-2024 |
| Basis | Withdrawals, million gallons per year by facility; one primary use per facility: public, hydro fracturing, misc, agriculture, golf course, mineral extraction, industry, power |
| Download | Scriptable (REST query with paging, or the weekly zip) |
| Caveats | County is the facility's location, not the water's source; mineral extraction is mostly quarry dewatering (show separately); return flows reported inconsistently (don't derive consumption); public-system customers don't register; no domestic wells |

Test values, Franklin County 2024: total 92,441 MG (252.6 Mgal/d; surface 58,575, ground 33,866); public 63,017 MG
(172.2 Mgal/d); mineral extraction 28,094 MG. Public 2023 60,242 MG, 2022 60,518 MG.

## Texas: TWDB Water Use Survey

| | |
|---|---|
| Data | Historical water use estimates, SARA report portal (`www3.twdb.texas.gov/apps/SARA/reports/list`), report 7 (by county, 2000 onward, with reuse) |
| Years | 2000-2024 |
| Basis | Acre-feet per year; municipal, manufacturing, mining, power, irrigation, livestock, each split ground, surface and reuse. "Use" is intake minus sales to others; steam-electric is consumptive only; irrigation and livestock are estimated |
| Download | Scriptable but brittle (an SSRS report viewer: session, report tokens, a form post, then the CSV export); keep dated copies |
| Caveats | Data centers are inside municipal; past years are revised; not directly comparable with USGS withdrawals |

Test values, Travis County 2024 (acre-feet): municipal 209,045 (186.6 Mgal/d; ground 19,511, surface 184,052, reuse
5,482); all categories 228,721 (204.2 Mgal/d). Ground + surface + reuse = total.

Context: TWDB surveyed 341 data centers for 2025 (about 17% responded); the 2027 State Water Plan has no data center
projections; HARC (Jan 2026) estimates about 25 billion gallons in 2025, direct plus power-plant water.

## Virginia: DEQ water withdrawal reporting

| | |
|---|---|
| Rule | 9VAC25-200: withdrawals averaging over 10,000 gal/day in any month (1 million gal/month for crop irrigation), reported monthly |
| Data | Annual Water Resources Report (2024 data in DEQ's Dec 2025 consolidated report, `rga.lis.virginia.gov/Published/2025/RD1017/PDF`): Table 21 locality totals, ground and surface, excluding power. Facility rows with use type in the Water Withdrawal Dashboard (`datascience.deq.virginia.gov/Water-Withdrawals-View/`, an R Shiny app) |
| Years | 1982-2024 |
| Basis | Gross withdrawals; DEQ does not estimate consumption. Use types: agriculture, irrigation, commercial (golf), industrial, mining, public water supply, fossil and nuclear power |
| Download | Locality totals: PDF table (stable, parses). Sector split: dashboard only (no direct download); a dated export, or a bulk request to DEQ |
| Caveats | Counted where water is taken (Loudoun buys from Fairfax Water); locality values can jump when an intake is reassigned (Prince William 70.1 to 2.6 Mgal/d, 2023 to 2024); public supply locations withheld below HUC12; dashboard and report disagree for Loudoun by about 4.8 Mgal/d |

Test values, Loudoun County: report Table 21, 2024 total 17.19 Mgal/d (ground 1.59, surface 15.61); 2023 17.58.
Dashboard 2024 public water supply about 11.8 Mgal/d (cross-check only).

Context: JLARC Report 598 (Dec 2024): data centers used about 2.1 billion gallons in 2023, a third of it reclaimed,
under 0.5% of state withdrawals; 0.2-21% of use at six utilities.

## As built (Oct 30, 2026)

`waterledger_data.wateruse`. Every layer returns `{"basis", "counties"}`: per county FIPS, Mgal/d by category (`mgd`,
`ground_mgd`, `surface_mgd`, and `reuse_mgd` for Texas), the source's own categories in its own units
(`source_values`), and, for USGS, public supply delivered to homes. Categories: public_supply, domestic, commercial,
industrial, irrigation, golf, livestock, aquaculture, mining, thermoelectric, other, total. A category the source has
no value for is left out, not set to zero. `place.context().supply.county_water_use` is the state's layer where there is
one, else USGS; `county_water_use_usgs` is always USGS (for deliveries to homes and comparison). Snapshots (format 2)
carry `wateruse.json` and the downloaded inputs under `inputs/wateruse/`.

| Layer | Function | Basis | Category mapping |
|---|---|---|---|
| USGS 2015 | `usgs_2015()` | estimate, withdrawals | PS, DO, CO, IN; irrigation IC + IR, golf IG; LI, AQ, MI; thermoelectric PO + PC |
| Ohio | `ohio()` | reported withdrawals, 2024 | Public, Industry, Power, Golf Course, Agriculture to irrigation, Mineral Extraction and Hydro Fracturing to mining, Misc to other |
| Texas | `texas()` | estimate (TWDB's "use"), 2024 | Municipal to public_supply, Manufacturing to industrial, Mining, Power to thermoelectric, Irrigation, LiveStock |
| Virginia | `virginia()` | reported withdrawals excluding power, 2024 | total only |
| Michigan | `states.mi.provider.egle_layer()` | reported withdrawals, 2025 | EGLE's groups as on the page; bottled water to industrial |

Decisions and deviations from the plan above:

- **USGS:** read from the release's parquet zip (the xlsx is the fallback; both hold the same table). The Dieter and
  Linsey 2018 CSV fallback is not built, since the revised file reads. Values: Franklin 155.82 / 188.31, Travis 122.10 /
  134.11, Loudoun 6.86 / 11.62 (delivered 27.08), Kent 9.01 / 27.76 (golf 1.91, delivered 31.78).
- **Ohio:** from the ArcGIS feature service (layer 0, tables 2 and 3, joined on RegistrationNumber, paged), years 2015
  onward cached. The latest complete year is the newest with at least 90% as many facilities reporting as the year
  before. ODNR's "Agriculture" is mostly crop, nursery and sod irrigation, with a few poultry and livestock farms, so it
  maps to irrigation. Hydraulic fracturing water is counted as mining, as USGS and TWDB do; ODNR's own use types stay
  apart in `source_values`. Million gallons a year are divided by the days in the year (366 for 2024): Franklin 2024
  public 63,017 MG (172.18 Mgal/d), total 92,441 MG (252.57).
- **Texas:** `fetch_twdb()` walks the report viewer (session, form post with the year, CSV export) and saves
  `county_<year>_<downloaded>.csv`; if the viewer changes it raises `SourceUnavailable` naming the step, and
  `texas(path=...)` reads a copy downloaded by hand or carried in a snapshot. Labeled an **estimate**, not reported:
  TWDB calls the series historical water use estimates, and rural domestic, irrigation, livestock and oil and gas mining
  are TWDB's estimates. From TWDB's definitions (updated Sept 23, 2023): municipal is public systems' intake less sales to
  other systems and industry, plus estimated self-supplied rural domestic use; data centers (NAICS 518210) fall in
  municipal; self-supplied golf courses are in irrigation; aquaculture is in livestock; steam-electric is consumption
  only; seawater is not counted. Acre-feet are divided by the days in the year: Travis 2024 municipal 209,045 acre-feet
  is 186.11 Mgal/d over 366 days (186.6 over 365, as above), total 228,721 is 203.63 (204.2).
- **Virginia:** Table 21 read with pypdf (now a dependency of waterledger-data: pure Python, no dependencies of its
  own); the PDF (about 80 MB) is downloaded once and the parsed table cached. Each row's ground plus surface must equal
  its total, and the columns must add up to the Total row's ground and surface within 2%. The 2024 Total row reads
  1,277.03 Mgal/d, but its rows add up to 1,181.36 (ground 151.32, surface 1,030.02, against the Total row's 152.31 and
  1,031.00): the rows are used as printed and the difference is noted in the basis. DEQ still lists three former
  cities; they are added to the counties that absorbed them (Bedford to Bedford County, which DEQ lists at 0.00 while
  the City of Bedford carries 19.14; Clifton Forge to Alleghany; South Boston to Halifax). 133 localities; Loudoun 17.19.
- Not built: Virginia's sector split (the dashboard has no bulk download), Ohio return flows, and USGS's newer modeled
  2020 layers.
