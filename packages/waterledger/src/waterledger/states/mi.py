"""Build Water Ledger Michigan's data files: <site>/mi/data/*.json.

Public data only. Every value carries a source id from SOURCES. Run from the repo root:
    python -m waterledger.states.mi              (or: waterledger build mi)
"""
import datetime, json, math, os, re

import pandas as pd

from waterledger_data import places as pl
from waterledger_data.climate import hourly_weather
from waterledger_models.datacenter import cooling as cw
from waterledger_models.datacenter import lake as lc
from waterledger_data.config import CACHE, SITE as SITE_ROOT, setting

from waterledger_models import MODEL_VERSION
STATE = "mi"      # Water Ledger is organized by state: site/waterledger/<state>/
SITE = os.path.join(SITE_ROOT, STATE)
OUT = os.path.join(SITE, "data", "estimates.json")
OUT_PLACES = os.path.join(SITE, "data", "places.json")
OUT_MAP = os.path.join(SITE, "data", "map.json")
OUT_WATERS = os.path.join(SITE, "data", "waters.json")
OUT_POWER = os.path.join(SITE, "data", "power.json")
RAW_BASE = CACHE
RAW_PLACES = os.path.join(RAW_BASE, "places")
RAW = os.path.join(RAW_BASE, "lit")

REGIONS = {
    "southeast": {"name": "Southeast Michigan", "station": "Ann Arbor area", "lat": 42.25, "lon": -83.60},
    "southwest": {"name": "Southwest Michigan", "station": "Kalamazoo area", "lat": 42.29, "lon": -85.59},
    "west": {"name": "West Michigan", "station": "Grand Rapids area", "lat": 42.88, "lon": -85.52, "cache": "gaines"},
    "central": {"name": "Central Michigan", "station": "Lansing area", "lat": 42.73, "lon": -84.55},
    "thumb": {"name": "Saginaw Valley and the Thumb", "station": "Saginaw area", "lat": 43.42, "lon": -83.95},
    "north": {"name": "Northwest Michigan", "station": "Traverse City area", "lat": 44.76, "lon": -85.62},
    "northeast": {"name": "Northeast Michigan", "station": "Alpena area", "lat": 45.06, "lon": -83.43},
    "up": {"name": "Central and Western Upper Peninsula", "station": "Marquette area", "lat": 46.54, "lon": -87.40},
}

SOURCES = {
    "lbnl2024": ("Shehabi, A., et al. (2024). 2024 United States Data Center Energy Usage Report. Lawrence Berkeley National Laboratory, LBNL-2001637.", "https://doi.org/10.71468/P1WC7Q"),
    "lei2022": ("Lei, N., & Masanet, E. (2022). Climate- and technology-specific PUE and WUE estimations for U.S. data centers using a hybrid statistical and thermodynamics-based approach. Resources, Conservation and Recycling 182: 106323.", "https://doi.org/10.1016/j.resconrec.2022.106323"),
    "lei2025": ("Lei, N., Lu, J., Shehabi, A., & Masanet, E. (2025). The water use of data center workloads: A review and assessment of key determinants. Resources, Conservation and Recycling 219: 108310.", "https://doi.org/10.1016/j.resconrec.2025.108310"),
    "usgs2013": ("Diehl, T. H., Harris, M. A., Murphy, J. C., Hutson, S. S., & Ladd, D. E. (2013). Methods for estimating water consumption for thermoelectric power plants in the United States. U.S. Geological Survey Scientific Investigations Report 2013-5188 (eq. 9 gives the Rutberg et al. 2011 dry-bulb evaporation relation).", "https://doi.org/10.3133/sir20135188"),
    "femp_bmp10": ("U.S. Department of Energy, Federal Energy Management Program. Best Management Practice #10: Cooling Tower Management.", "https://www.energy.gov/femp/best-management-practice-10-cooling-tower-management"),
    "femp_dc": ("U.S. Department of Energy, FEMP. Cooling Water Efficiency Opportunities for Federal Data Centers.", "https://www.energy.gov/cmei/femp/cooling-water-efficiency-opportunities-federal-data-centers"),
    "epa_wsaw": ("U.S. EPA (2012). WaterSense at Work: Best Management Practices for Commercial and Institutional Facilities, §6.3 Cooling Towers.", "https://www.epa.gov/watersense/best-management-practices"),
    "stull2011": ("Stull, R. (2011). Wet-bulb temperature from relative humidity and air temperature. Journal of Applied Meteorology and Climatology 50: 2267–2269.", "https://doi.org/10.1175/JAMC-D-11-0143.1"),
    "msft2026": ("Microsoft (June 24, 2026). Inside Microsoft's two-decade push to cut water intensity while scaling for growth.", "https://blogs.microsoft.com/blog/2026/06/24/inside-microsofts-two-decade-push-to-cut-water-intensity-while-scaling-for-growth/"),
    "icprb2025": ("Interstate Commission on the Potomac River Basin (2025). 2025 Washington Metropolitan Area Water Supply Study (ICP-596), §6.2 and Table 6-5.", "https://www.potomacriver.org/publications/2025-washington-metropolitan-area-water-supply-study-demand-and-resource-availability-forecast-for-the-year-2050/"),
    "icprb2026": ("Interstate Commission on the Potomac River Basin (March 2026). Data Centers and Water Use in the Potomac River Basin (fact sheet).", "https://www.potomacriver.org/wp-content/uploads/2026/03/ICPRB.DataCentersandWaterUse.ICPRB_.March2026.pdf"),
    "siddik2024": ("Siddik, M. A. B., Shehabi, A., Rao, P., & Marston, L. T. (2024). Spatially and temporally detailed water and carbon footprints of U.S. electricity generation and use. Water Resources Research 60(12). Data: LBNL Water IMPACT (HydroShare), 2022 v1.1.", "https://doi.org/10.1029/2024WR038350"),
    "macknick2012": ("Macknick, J., et al. (2012). Operational water consumption and withdrawal factors for electricity generating technologies. Environmental Research Letters 7: 045802.", "https://doi.org/10.1088/1748-9326/7/4/045802"),
    "peer2019": ("Peer, R. A. M., Grubert, E., & Sanders, K. T. (2019). A regional assessment of the water embedded in the US electricity system. Environmental Research Letters 14: 084014.", "https://doi.org/10.1088/1748-9326/ab2daa"),
    "eia_mi": ("U.S. Energy Information Administration. Michigan electricity profile and EIA-923 generation data (2025).", "https://www.eia.gov/electricity/state/michigan/"),
    "gcsaa2013": ("GCSAA (2015). Golf Course Environmental Profile: water use and conservation practices on U.S. golf courses (2013 survey, by region).", "https://gcsaa.org/docs/default-source/Environment/phase-2-water-use-survey-full-report.pdf"),
    "usgs_cu2007": ("Shaffer, K. H., & Runkle, D. L. (2007). Consumptive water-use coefficients for the Great Lakes Basin and climatically similar areas. USGS Scientific Investigations Report 2007-5197 (commercial use: about 10% consumed).", "https://pubs.usgs.gov/sir/2007/5197/"),
    "energystar_humid": ("U.S. EPA ENERGY STAR. 16 more ways to cut energy waste in the data center: make humidification adjustments (data centers in cool climates, particularly with free cooling, should not need to humidify for much of the year; after ASHRAE TC 9.9's 2014 electrostatic discharge study).", "https://www.energystar.gov/products/data_center_equipment/16-more-ways-cut-energy-waste-data-center/make-humidification-adjustments"),
    "jlarc2024": ("Joint Legislative Audit and Review Commission, Virginia (December 9, 2024). Data Centers in Virginia 2024. Report 598 (a typical building: about 50 full-time workers once open, about half of them contractors).", "https://jlarc.virginia.gov/pdfs/reports/Rpt598.pdf"),
    "mcl_205_54ee": ("Michigan General Sales Tax Act, MCL 205.54ee: data center equipment exemption (an enterprise data center needs at least 30 new jobs, among other conditions).", "https://legislature.mi.gov/Laws/MCL?objectName=mcl-205-54ee"),
    "lowell_firstlook": ("Lowell's First Look (May 2026), citing Microsoft: about 2.2 million gallons a year excluding cooling, plus a one-time 1.2 million gallon fill; Lowell Township business park page. Primary document not yet located.", "https://www.lowelltwp.org/business_park/index.php"),
    "gaines_sunnews": ("Sun and News / WOOD TV (2026): Microsoft at the April 15, 2026 Gaines Township hearing, about 2,000 gallons a day per building.", "https://www.yahoo.com/news/articles/gaines-township-research-noise-proposed-215143809.html"),
    "saline_post": ("The Saline Post (July 2026), as reported by Planet Detroit and Sun Times News: about 20,000 gallons a day at the start of operations, a developer estimate. Primary document not yet located.", "https://planetdetroit.org/2025/10/saline-data-center-settlement/"),
    "wgvu_switch": ("WGVU (December 16, 2025): Gaines Township's community development director, about 10 million gallons last year at the Switch data center (design 320 MW, Switch 2017; actual load not public).", "https://www.wgvunews.org/news/2025-12-16/gaines-township-to-consider-rezoning-for-future-microsoft-data-center"),
    "nih_closedloop": ("NIH Office of Research Facilities (August 2023). Closed Loop Water Treatment, Technical Bulletin: closed systems typically need makeup water of less than 5% of their volume a year.", "https://orf.od.nih.gov/TechnicalResources/Documents/Technical%20Bulletins/23TB/Closed%20Loop%20Water%20Treatment%20-%20August%202023%20Technical%20Bulletin_508.pdf"),
    "mpsc_territory": ("Michigan Public Service Commission. Electric Utility Service Areas (GIS hub, 2025): territories of Michigan's investor-owned, cooperative and municipal electric utilities.", "https://data-michiganpsc.hub.arcgis.com"),
    "eia861": ("U.S. Energy Information Administration. Annual Electric Power Industry Report (Form EIA-861), 2025: retail sales and customers by utility and state, and summer and winter peak demand.", "https://www.eia.gov/electricity/data/eia861/"),
    "egle2025": ("Michigan EGLE. Water Use Data, 2025 (by county and sector; reported by registered large-quantity withdrawals).", "https://www.michigan.gov/egle/about/organization/geologic-resources-management/groundwater/water-use/reporting/water-use-data"),
    "epa_watersense": ("U.S. EPA WaterSense. How We Use Water: \"The average American family uses more than 300 gallons of water per day at home.\"", "https://www.epa.gov/watersense/how-we-use-water"),
    "era5": ("Hourly 2 m temperature and humidity, 1995–2024, ECMWF ERA5 reanalysis via the Open-Meteo archive API.", "https://open-meteo.com/en/docs/historical-weather-api"),
    "google2026": ("Google (2026). 2026 Environmental Report (data for 2025), data center water tables.", "https://storage.googleapis.com/gweb-mobius-cdn/sustainability/uploads/7f477eb723fe0c23d03f94b90a08882b9f28187d.pdf"),
    "han2026": ("Han, Y., Li, P., Wierman, A., & Ren, S. (2026). Small Bottle, Big Pipe: Quantifying and addressing the impact of data centers on public water systems. arXiv:2603.02705 (preprint, not peer reviewed).", "https://arxiv.org/abs/2603.02705"),
    "census_tiger": ("U.S. Census Bureau. TIGERweb county subdivisions (cities and townships) and counties, Michigan.", "https://tigerweb.geo.census.gov/"),
    "epa_sa": ("U.S. EPA. Community Water System Service Area Boundaries (reported or modeled), with population served and connections from SDWIS.", "https://www.epa.gov/ground-water-and-drinking-water/community-water-system-service-area-boundaries"),
    "usgs_wbd": ("U.S. Geological Survey. Watershed Boundary Dataset (HUC8 and HUC12).", "https://www.usgs.gov/national-hydrography/watershed-boundary-dataset"),
    "noaa_atlas14": ("NOAA National Weather Service. Atlas 14, Volume 8 (Midwestern States), precipitation frequency estimates.", "https://hdsc.nws.noaa.gov/pfds/"),
    "simple_method": ("Schueler, T. (1987). The Simple Method: runoff coefficient Rv = 0.05 + 0.009 × percent impervious (as used in EPA and state stormwater guidance).", "https://www.epa.gov/npdes/national-menu-best-management-practices-bmps-stormwater"),
    "egle_impaired": ("Michigan EGLE. Water Quality and Pollution Control in Michigan: Sections 303(d), 305(b) and 314 Integrated Report (impaired waters and TMDLs).", "https://www.michigan.gov/egle/about/organization/water-resources/glwarm/integrated-report"),
    "mcl327": ("Michigan Natural Resources and Environmental Protection Act, Part 327 Great Lakes Preservation: MCL 324.32701 (large quantity withdrawal: over 100,000 gallons a day averaged over any 30 days; waters of the state include the Great Lakes) and MCL 324.32723 (withdrawal permits: new withdrawals over 2,000,000 gallons a day, or over 1,000,000 in Zone C).", "https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-324-32723"),
    "wgvu2026": ("Limbaugh, D. (2026, May 26). Unregulated demands: how rising data center water use avoids Great Lakes Compact scrutiny. WGVU News. (Compact regional review at 5 million gallons a day of consumptive use, averaged over 90 days; most data centers connect to public water systems.)", "https://www.wgvunews.org/news/2026-05-26/unregulated-demands-how-rising-data-center-water-use-avoids-great-lakes-compact-scrutiny"),
    "eia_res": ("U.S. Energy Information Administration (2025). Electric Sales, Revenue, and Average Price, 2024 data, Table 5A: residential average monthly bill by state. Michigan: 4,516,367 residential customers, 618 kWh per month on average.", "https://www.eia.gov/electricity/sales_revenue_price/"),
    "msft2024": ("Solomon, S. (2024, December 9). Sustainable by design: Next-generation datacenters consume zero water for cooling. Microsoft Cloud blog. (Replacing evaporative cooling with chillers raises PUE: \"a nominal increase in our annual energy usage.\")", "https://www.microsoft.com/en-us/microsoft-cloud/blog/?p=251"),
    "glerl": ("NOAA Great Lakes Environmental Research Laboratory. Great Lakes Long Term Average Surface Water Temperature, Daily (GLSEA).", "https://apps.glerl.noaa.gov/erddap/info/glerlLTAvgTemp/index.html"),
    "lsc_cornell": ("7x24 Exchange (2014, Spring). Lake and river source cooling, magazine p. 26: Cornell Lake Source Cooling draws Cayuga Lake water at about 39 °F (3.9 °C) from 250 ft and returns it at about 56 °F (13.3 °C); Toronto's Enwave deep lake system draws 4 °C water from 83 m.", "https://7x24exchange.org/spring14_/7x24_Spring_Magazine/files/assets/basic-html/page26.html"),
    "cfr125_81": ("40 CFR 125.81. Cooling water intake structures, new facilities: applies to point sources with a design intake flow over 2 million gallons a day that use at least 25% of the water withdrawn for cooling.", "https://www.law.cornell.edu/cfr/text/40/125.81"),
    "mi_part22": ("Michigan Administrative Code, Part 22 groundwater quality rules: R 323.2210 (sanitary sewage under 6,000 gallons a day to a septic system approved by the county, district or city health department needs no state permit), R 323.2211 (6,000 to 10,000 gallons a day: permit by rule, health department approval, metered flow reported yearly) and R 323.2216 (larger sanitary discharges under an EGLE groundwater discharge permit).", "https://www.law.cornell.edu/regulations/michigan/Mich-Admin-Code-R-323-2210"),
    "egle_npdes": ("Michigan EGLE. National Pollutant Discharge Elimination System (NPDES) program: rules and regulations (Part 31, Water Resources Protection, NREPA). Discharges of wastewater to surface waters need a permit.", "https://www.michigan.gov/egle/about/Organization/Water-Resources/npdes/rules-and-regulations"),
    "naturalearth": ("Natural Earth. 1:50m lakes and states/provinces (shorelines, generalized). Public domain.", "https://www.naturalearthdata.com/downloads/50m-physical-vectors/"),
    "mytton2021": ("Mytton, D. (2021). Data centre water consumption. npj Clean Water 4: 11.", "https://doi.org/10.1038/s41545-021-00101-w"),
    # receiving waters, runoff quality, salt, fuel and sewer plants
    "attains2026": ("U.S. EPA ATTAINS, Michigan 2026 Integrated Report assessment units and parameters (EGLE's Clean Water Act 303(d) and 305(b) listings; category 4A = TMDL in place), via the ATTAINS_Assessment map service.", "https://gispub.epa.gov/arcgis/rest/services/OW/ATTAINS_Assessment/MapServer"),
    "mdnr_trout": ("Michigan DNR. Trout and Salmon Regulations, Stream Main (designated trout streams, active segments). Designated trout streams are coldwater under R 323.1100(7).", "https://services3.arcgis.com/Jdnp1TjADvSDxMAX/ArcGIS/rest/services/DNRFisheriesTroutRegsOPENDATA/FeatureServer/0"),
    "noaa_cag": ("NOAA NCEI. Climate at a Glance, county time series (nClimGrid): annual precipitation, mean of 1991–2020.", "https://www.ncei.noaa.gov/access/monitoring/climate-at-a-glance/county/time-series"),
    "echo": ("U.S. EPA ECHO, Clean Water Act facility search, Michigan publicly owned treatment works: location, receiving water, combined sewer flag and the past calendar year's average reported flow.", "https://echo.epa.gov/"),
    "cwns2022": ("U.S. EPA Clean Watersheds Needs Survey 2022, current design flow by facility (Hodson et al. 2026 HydroShare compilation, CC BY 4.0). CWNS has no actual flows.", "https://www.hydroshare.org/resource/3dab07fd628a4af2ba812f038b1af89f/"),
    "usgs_marquette": ("Steuer, J., Selbig, W., Hornewer, N., & Prey, J. (1997). Sources of contamination in an urban basin in Marquette, Michigan, and an analysis of concentrations, loads, and data quality. USGS Water-Resources Investigations Report 97-4242, Table 4 (rooftops, parking lots).", "https://pubs.usgs.gov/wri/1997/4242/report.pdf"),
    "mpca_emc": ("Minnesota Pollution Control Agency. Minnesota Stormwater Manual: event mean concentrations of total suspended solids and of total phosphorus in stormwater runoff, by land use.", "https://stormwater.pca.state.mn.us/node/6015"),
    "nsqd": ("Pitt, R. (2011). The National Stormwater Quality Database, Version 3.1, Tables 2–4 (EPA Rain Zone 1, which includes Michigan).", "https://yosemite.epa.gov/oa/eab_web_docket.nsf/Attachments%20By%20ParentFilingId/0579A9DB19C5446F85257CBA00593372/$FILE/Attachment%202%20-%20Pitt%2C%20National%20Stormwater%20Quality%20Database%20Version%203.1.pdf"),
    "stepl": ("Tetra Tech for U.S. EPA (2018). Spreadsheet Tool for Estimating Pollutant Loads (STEPL) 4.4 User's Guide: urban and cropland/forest runoff concentrations.", "https://19january2021snapshot.epa.gov/sites/static/files/2021-01/documents/steplguide404.pdf"),
    "egle_ms4": ("Michigan EGLE MS4 permit post-construction standard (example: Charter Township of Lansing, NPDES MI0059459, effective July 1, 2025, Part I.A.f): treat the first inch or 90% of runoff-producing storms with 80% TSS removal or 80 mg/L; hold rate and volume to pre-development up to the 2-year, 24-hour storm.", "https://lansingtwpmi.gov/wp-content/uploads/2026/05/Lansing-Township-Appendix-A-Stormwater-Discharge-Permit-and-Application-4-2026.pdf"),
    "kcdc_rules": ("Kent County Drain Commissioner (2024). Site Development Rules, Procedures and Design Standards for Stormwater Management, rev. Dec 27, 2024 (Table 3 TSS removal; coldwater detention limits; applicability).", "https://www.kentcountymi.gov/DocumentCenter/View/2402/Site-Development-Rules-Procedures-and-Design-Standards-for-Stormwater-Management-PDF"),
    "bmpdb2020": ("Clary, J., et al. (2020). International Stormwater BMP Database: 2020 Summary Statistics. Water Research Foundation Project 4968, Tables 2-2, 4-3 and 4-6 (wet pond medians in and out).", "https://www.waterrf.org/system/files/resource/2020-11/DRPT-4968_0.pdf"),
    "semcog_lid": ("SEMCOG (2008). Low Impact Development Manual for Michigan, Table 9.5 (pollutant removal by practice, after the Center for Watershed Protection database).", "https://www.swmpc.org/wp-content/uploads//2026/01/lidmanual_1.pdf"),
    "epa_fact26": ("U.S. EPA (2005). Stormwater Phase II Final Rule Fact Sheet 2.6, Construction Site Runoff Control: sediment runoff from construction sites is typically 10 to 20 times that of agricultural lands.", "https://www.epa.gov/sites/default/files/2015-11/documents/fact2-6.pdf"),
    "epa_mm8": ("U.S. EPA (2005). National Management Measures to Control Nonpoint Source Pollution from Urban Areas, Management Measure 8 (construction), p. 8-2 and Table 8.1: construction sites 7.2 to 500 tons per acre per year; Wisconsin 30 to 200.", "https://www.epa.gov/sites/default/files/2015-09/documents/urban_ch08.pdf"),
    "part91": ("Michigan Part 91 Soil Erosion and Sedimentation Control rules, R 323.1704(1): permit for earth changes of 1 acre or more or within 500 feet of a lake or stream; construction storm water permit-by-rule, R 323.2190.", "https://www.law.cornell.edu/regulations/michigan/Mich-Admin-Code-R-323-2190"),
    "mpca_salt": ("Minnesota Pollution Control Agency (2023). Deicer fact sheet and application rate guidance (p-tr1-20): 0.75 to 3.0 lb of dry salt per 1,000 sq ft per event, by pavement temperature.", "https://www.pca.state.mn.us/sites/default/files/p-tr1-20.pdf"),
    "egle_rule57": ("Michigan EGLE. Rule 57 Water Quality Values: chloride final chronic value 150 mg/L, aquatic maximum value 320 mg/L.", "https://www.michigan.gov/egle/about/organization/water-resources/glwarm/rule-57-water-quality-values"),
    "cat3516c": ("Caterpillar. 3516C diesel generator set, 60 Hz, 1,650–2,000 ekW, spec sheet LEHE1376-09 (2023): 133.6 gal/h at 2,000 ekW standby, 100% load.", "https://penncatenergy.com/wp-content/uploads/2025/12/3516C-60-Hz-1650-2000-ekW-Spec-Sheet.pdf"),
    "uptime2014": ("Heslin, K. (2014, June 18). Fuel system design and reliability. Uptime Institute Journal: the Tier Standard requires at least 12 hours of on-site fuel at N load.", "https://journal.uptimeinstitute.com/?p=3233"),
    "amazon_mo2026": ("Ramboll for Amazon Data Services (May 2026). Air permit application, STL100 data center, New Florence, Missouri, to Missouri DNR: 476 generators of 2.75 MW with belly tanks and bulk storage (about 3.3 million gallons by Northline's reading of the tank table).", "https://dnr.mo.gov/sites/dnr/files/vfc/2026/05/main/amazon-data-center-new-florence-complete-application-may-2026.pdf"),
    "wyofile2025": ("Bleizeffer, D. (2025, May 12). WyoFile: Microsoft's Cheyenne data centers, 128 generators and tanks holding up to 1.8 million gallons of diesel (per Wyoming DEQ).", "https://wyofile.com/"),
    "cfr112": ("40 CFR 112 (Spill Prevention, Control, and Countermeasure): applies above 1,320 gallons of aboveground oil storage. Michigan Part 5 rules (R 324.2001 et seq.) add a Pollution Incident Prevention Plan for oil and salt above threshold quantities.", "https://www.law.cornell.edu/cfr/text/40/112.1"),
    "herb2007": ("Herb, W., Janke, B., Mohseni, O., & Stefan, H. (2007). Estimation of runoff temperatures and heat export from different land and water surfaces. St. Anthony Falls Laboratory, University of Minnesota: average runoff temperature 24.9 °C from concrete vs 21.5 °C from forest.", "http://purl.umn.edu/113694"),
    "stefan2010": ("Stefan, H., & Herb, W. (2010). SAFL Project Report 541 for MPCA: wet ponds add heat; infiltration is highly effective at reducing thermal loads from runoff.", "https://conservancy.umn.edu/server/api/core/bitstreams/80619f96-ab42-49bd-81e1-5804f5f9c61b/content"),
    "rule75": ("Michigan Water Quality Standards, R 323.1075 (temperature): coldwater streams may not be warmed more than 2 °F above natural; monthly maximum 68 °F in June, July and August.", "https://www.law.cornell.edu/regulations/michigan/Mich-Admin-Code-R-323-1075"),
    "jea2024": ("JEA (2024). Best Management Practice and Guidance Manual for Cooling Towers, Table 1: phosphate inhibitors up to 20 mg/L as PO4 (about 6.5 mg/L as P), molybdate, azoles, biocides in blowdown.", "https://www.jea.com/uploadedFiles/jea.com/Business_Resources/Industrial_Pretreatment/Commercial_Best_Management_Practices/JEA%20Cooling%20Tower%20BMP%20v.2024-CURRENT.pdf"),
    "rule60": ("Michigan Water Quality Standards, R 323.1060: default effluent limit of 1 mg/L total phosphorus (monthly average) for point sources.", "https://www.law.cornell.edu/regulations/michigan/Mich-Admin-Code-R-323-1060"),
    "egle_dc_faq": ("Michigan EGLE. FAQ: Data centers and environmental review (data centers are not categorical industrial users but may be designated significant industrial users; only plants with approved pretreatment programs can issue discharge permits).", "https://www.michigan.gov/egle/faqs/environmental-assistance/data-centers"),
    "nri2017": ("USDA NRCS (2020). 2017 National Resources Inventory Summary Report: sheet and rill erosion on U.S. cropland averaged 2.67 tons per acre per year in 2017.", "https://www.nrcs.usda.gov/sites/default/files/2022-10/2017NRISummary_Final.pdf"),
    "wellogic": ("Michigan EGLE. Wellogic water well records: household wells by township, the aquifer each draws from (glacial deposits or bedrock), well depth and static water level.", "https://gisagoegle.state.mi.us/arcgis/rest/services/EGLE/DwOpenData/MapServer/3"),
    "wwat": ("Michigan EGLE. Water Withdrawal Assessment Tool (Part 327): new or increased withdrawals over 100,000 gallons a day are screened for how much they would reduce nearby streams' summer flow and harm their fish.", "https://www.egle.state.mi.us/wwat/"),
    "wleb_dap": ("MDARD, EGLE and DNR. Michigan's Domestic Action Plan for the Western Lake Erie Basin (2025 update): a 40% cut in phosphorus loads from 2008 levels.", "https://www.michigan.gov/mdard/environment/conservation/wleb"),
}

SHORT = {"lbnl2024": "LBNL 2024", "lei2022": "Lei & Masanet 2022", "lei2025": "Lei et al. 2025", "usgs2013": "USGS 2013", "femp_bmp10": "DOE FEMP",
         "femp_dc": "DOE FEMP", "epa_wsaw": "EPA 2012", "stull2011": "Stull 2011", "msft2026": "Microsoft 2026", "icprb2025": "ICPRB 2025",
         "icprb2026": "ICPRB 2026", "siddik2024": "Siddik et al. 2024", "macknick2012": "Macknick et al. 2012", "peer2019": "Peer et al. 2019",
         "eia_mi": "EIA", "egle2025": "EGLE 2025", "mpsc_territory": "MPSC", "usgs_cu2007": "Shaffer & Runkle 2007", "energystar_humid": "ENERGY STAR", "nih_closedloop": "NIH 2023", "jlarc2024": "JLARC 2024", "mcl_205_54ee": "MCL 205.54ee", "lowell_firstlook": "Lowell's First Look", "gaines_sunnews": "Sun and News 2026", "saline_post": "The Saline Post", "wgvu_switch": "WGVU 2025", "eia861": "EIA-861", "gcsaa2013": "GCSAA 2013", "epa_watersense": "EPA WaterSense", "era5": "ERA5", "google2026": "Google 2026",
         "han2026": "Han et al. 2026", "mytton2021": "Mytton 2021", "census_tiger": "Census", "epa_sa": "EPA service areas", "usgs_wbd": "USGS WBD",
         "noaa_atlas14": "NOAA Atlas 14", "simple_method": "Simple Method", "egle_impaired": "EGLE", "mcl327": "MCL Part 327", "wgvu2026": "WGVU 2026", "naturalearth": "Natural Earth", "glerl": "NOAA GLERL", "eia_res": "EIA 2024", "msft2024": "Microsoft 2024", "lsc_cornell": "Cornell LSC", "cfr125_81": "40 CFR 125.81", "egle_npdes": "EGLE NPDES", "mi_part22": "Mich. Part 22 rules",
         "attains2026": "EPA ATTAINS 2026", "mdnr_trout": "Michigan DNR trout streams", "noaa_cag": "NOAA 1991–2020", "echo": "EPA ECHO", "cwns2022": "EPA CWNS 2022",
         "usgs_marquette": "USGS Marquette 1997", "mpca_emc": "MPCA", "nsqd": "NSQD", "stepl": "EPA STEPL", "egle_ms4": "EGLE MS4 standard", "kcdc_rules": "Kent County rules",
         "bmpdb2020": "BMP Database 2020", "semcog_lid": "SEMCOG 2008", "epa_fact26": "EPA 2005", "epa_mm8": "EPA MM8", "part91": "Part 91", "mpca_salt": "MPCA salt guidance",
         "egle_rule57": "EGLE Rule 57", "cat3516c": "Caterpillar", "uptime2014": "Uptime Institute", "amazon_mo2026": "Amazon MO permit", "wyofile2025": "WyoFile 2025",
         "cfr112": "40 CFR 112", "herb2007": "Herb et al. 2007", "stefan2010": "Stefan & Herb 2010", "rule75": "R 323.1075", "jea2024": "JEA 2024", "rule60": "R 323.1060",
         "egle_dc_faq": "EGLE data center FAQ", "wleb_dap": "Lake Erie action plan", "nri2017": "USDA NRI 2017", "wellogic": "EGLE Wellogic", "wwat": "EGLE WWAT"}

PARAM_SOURCES = {
    "utilization": ["lbnl2024"], "hf_econ": ["femp_dc"], "hf_chiller": ["femp_dc"], "wb_econ": ["femp_dc"], "wb_chiller": ["femp_dc"],
    "er_adj": ["usgs2013"], "coc": ["femp_bmp10"], "range_f": ["usgs2013"], "drift": ["epa_wsaw"], "fill_gal_per_mw": ["lowell_firstlook"], "topup": ["nih_closedloop"],
    "staff_core": ["jlarc2024", "mcl_205_54ee"], "staff_per_mw": ["jlarc2024"], "staff_gpcd": [], "staff_used": ["usgs_cu2007"],
    "assist_on": ["msft2026"], "assist_share": ["lei2025"], "hybrid_on": ["lei2025", "han2026"], "hybrid_full": ["lei2025"],
}

POWER = {
    "consumed_l_per_kwh": {"michigan_mix": 0.9, "miso_excl_hydro": 1.57, "miso_incl_hydro": 3.84,
                           "range": [0.68, 1.31], "sources": ["eia_mi", "macknick2012", "egle2025", "peer2019", "siddik2024"]},
    "withdrawn_l_per_kwh": {"value": 57.0, "returned_share_note": "about 99% returned to the Great Lakes and rivers, warmer", "sources": ["siddik2024", "egle2025"]},
}

# Electricity overhead by cooling design: LBNL 2024 Fig. 4.4, large-scale facilities, simulated annual PUE (figure-read medians and boxes,
# U.S. climates). Closed loop spans LBNL's two waterless large-scale systems: liquid-cooled IT with dry coolers (about 1.10) and dry coolers
# with an air-cooled chiller (about 1.20). Lake-source is not in LBNL; the cooling-tower range stands in for it [estimate].
PUE_DESIGN = {
    "dry": {"lo": 1.07, "mid": 1.15, "hi": 1.24, "basis": "LBNL 2024: liquid-cooled IT with dry coolers (median about 1.10) to dry coolers with air-cooled chillers (about 1.20)"},
    "assist": {"lo": 1.07, "mid": 1.15, "hi": 1.24, "basis": "LBNL 2024: dry coolers with adiabatic assist, liquid-cooled IT (about 1.10) or air-cooled chiller (about 1.20)"},
    "hybrid": {"lo": 1.11, "mid": 1.14, "hi": 1.17, "basis": "LBNL 2024: airside economizer with adiabatic cooling and water-cooled chiller"},
    "towers": {"lo": 1.09, "mid": 1.12, "hi": 1.16, "basis": "LBNL 2024: waterside economizer with water-cooled chiller, air- or liquid-cooled IT"},
    "lake": {"lo": 1.09, "mid": 1.12, "hi": 1.16, "basis": "Not simulated by LBNL; the cooling-tower range stands in [estimate]"},
}

# Water consumed at power plants per MWh, by what supplies the campus (gallons per MWh; Macknick et al. 2012 medians and ranges unless noted).
POWER_SUPPLY = {
    "mi_mix": {"label": "Michigan's current mix", "gal_mwh": 238, "lo": 180, "hi": 346, "sources": ["eia_mi", "macknick2012", "egle2025"],
               "note": "0.9 L/kWh (0.68 to 1.31): EIA 2025 generation mix with Macknick factors, checked against EGLE's reported power-sector use"},
    "new_gas": {"label": "Gas plants", "gal_mwh": 205, "lo": 130, "hi": 300, "sources": ["macknick2012"],
                "note": "Natural gas combined cycle with cooling towers"},
    # Michigan's own plants (model 1.2; before, cooling-tower plants): the large coal plants (Monroe, Belle River, Campbell) and Cook
    # nuclear are cooled with lake or river water passing through once; Fermi 2 has cooling towers. Nuclear weights Cook's two-thirds of
    # Michigan's nuclear generation once-through and Fermi's third with towers. Same factors as the Michigan mix above.
    "coal": {"label": "Michigan's coal plants", "gal_mwh": 250, "lo": 100, "hi": 317, "sources": ["macknick2012", "eia_mi"],
             "note": "Coal cooled with lake or river water passing through once, as Michigan's large coal plants are"},
    "nuclear": {"label": "Michigan's nuclear plants", "gal_mwh": 403, "lo": 260, "hi": 548, "sources": ["macknick2012", "eia_mi"],
                "note": "Cook (about two-thirds of Michigan's nuclear generation) cooled with Lake Michigan water passing through once; Fermi 2 with cooling towers"},
    "renew": {"label": "Wind and solar", "gal_mwh": 1, "lo": 0, "hi": 5, "sources": ["macknick2012"], "note": "Wind 0; utility solar about 1 (0 to 5) for panel washing"},
    "miso": {"label": "MISO grid average", "gal_mwh": 415, "lo": 415, "hi": 415, "sources": ["siddik2024"], "note": "1.57 L/kWh, MISO excluding hydropower"},
}

CONTEXT = {"household_gpd": {"value": 300, "note": "more than 300 gallons per day per family at home", "sources": ["epa_watersense"]}}

TRACKER_MUNI = {"gaines": ("Gaines charter township", "Kent"), "lowell": ("Lowell charter township", "Kent"), "dorr": ("Dorr township", "Allegan"),
                "ypsi": ("Ypsilanti charter township", "Washtenaw"), "augusta": ("Augusta charter township", "Washtenaw"), "saline": ("Saline township", "Washtenaw"),
                "vanburen": ("Van Buren charter township", "Wayne"), "lyon": ("Lyon charter township", "Oakland"), "southfield": ("Southfield city", "Oakland"),
                "howell": ("Howell township", "Livingston")}

LON0, LON1, LAT0, LAT1 = -90.5, -82.3, 41.65, 48.35
KX, SC = math.cos(math.radians(45)), 60.0


def proj(lon, lat):
    return round((lon - LON0) * KX * SC, 1), round((LAT1 - lat) * SC, 1)


def _dp(pts, tol):
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1e-9
    i, dmax = 0, 0
    for k, (x, y) in enumerate(pts[1:-1], 1):
        d = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / L
        if d > dmax:
            i, dmax = k, d
    if dmax > tol:
        return _dp(pts[:i + 1], tol)[:-1] + _dp(pts[i:], tol)
    return [pts[0], pts[-1]]


def _ring_path(ring, tol, minpts=4):
    p = [proj(*c[:2]) for c in ring]
    p = p[:-1] if p[0] == p[-1] else p
    m = len(p) // 2
    p = _dp(p[:m + 1], tol)[:-1] + _dp(p[m:] + [p[0]], tol)[:-1]
    if len(p) < minpts:
        return ""
    return "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in p) + "Z"


def _geom_path(geom, tol, minpts=4):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    return "".join(_ring_path(r, tol, minpts) for poly in polys for r in poly)


def nearest_region(lat, lon):
    def d(r):
        return (lat - r["lat"]) ** 2 + ((lon - r["lon"]) * math.cos(math.radians(lat))) ** 2
    return min(REGIONS, key=lambda k: d(REGIONS[k]))


def build_map(counties):
    adm = json.load(open(os.path.join(RAW_PLACES, "adm50.json")))
    mi = [f["geometry"] for f in adm["features"] if f["properties"].get("name") == "Michigan" and f["properties"].get("admin") == "United States of America"][0]
    lakes = json.load(open(os.path.join(RAW_PLACES, "lakes50.json")))
    lk = [f["geometry"] for f in lakes["features"] if f["properties"].get("name") in ("Lake Superior", "Lake Michigan", "Lake Huron", "Lake Erie", "Lake Saint Clair")]
    W, H = proj(LON1, LAT0)
    out = {"viewBox": f"0 0 {W} {H}", "land": _geom_path(mi, 0.25), "lakes": "".join(_geom_path(g, 0.35, 6) for g in lk),
           "counties": {}, "stations": {k: dict(zip(("x", "y"), proj(r["lon"], r["lat"]))) for k, r in REGIONS.items()},
           "source": "County lines: U.S. Census TIGERweb; shoreline and lakes: Natural Earth 1:50m"}
    for c in counties:
        out["counties"][c["geoid"]] = {"name": c["name"], "region": nearest_region(c["lat"], c["lon"]),
                                       "d": "".join(_ring_path(r, 0.2, 3) for r in c["rings"])}
    return out


GREAT_LAKES = ("Lake Superior", "Lake Michigan", "Lake Huron", "Lake Erie", "Lake Saint Clair")
SHORE_KM = 5.0


def great_lake_near(bounds):
    """Nearest Great Lake (or Lake St. Clair) within SHORE_KM of each municipal boundary (Natural Earth 1:50m shoreline; Census boundaries)."""
    import numpy as np
    lakes = json.load(open(os.path.join(RAW_PLACES, "lakes50.json")))
    pts = {}
    for f in lakes["features"]:
        n = f["properties"].get("name")
        if n in GREAT_LAKES:
            polys = f["geometry"]["coordinates"] if f["geometry"]["type"] == "MultiPolygon" else [f["geometry"]["coordinates"]]
            pts[n] = np.array([pt for poly in polys for ring in poly for pt in ring])
    kx = 111.32 * math.cos(math.radians(44.5))
    out = {}
    for gid, rings in bounds.items():
        b = np.array([pt for r in rings for pt in r])
        x0, y0 = b.min(0) - 0.1
        x1, y1 = b.max(0) + 0.1
        best = None
        for n, L in pts.items():
            near = L[(L[:, 0] >= x0) & (L[:, 0] <= x1) & (L[:, 1] >= y0) & (L[:, 1] <= y1)]
            if not len(near):
                continue
            d = np.sqrt((((b[:, None, 0] - near[None, :, 0]) * kx) ** 2 + ((b[:, None, 1] - near[None, :, 1]) * 110.95) ** 2)).min()
            if d <= SHORE_KM and (best is None or d < best[1]):
                best = (n.replace("Saint", "St."), round(float(d), 1))
        if best:
            out[gid] = {"lake": best[0], "km": best[1]}
    return out


def build_places(counties, munis, enrich, cmap, shore=None):
    shore = shore or {}
    cname = {c["geoid"]: c["name"] for c in counties}
    out = []
    for m in munis:
        e = enrich.get(m["geoid"], {})
        x, y = proj(m["lon"], m["lat"])
        ws = e.get("watershed", {})
        out.append({"g": m["geoid"], "n": m["name"], "k": m["kind"], "c": cname.get(m["county_fips"], ""), "cf": m["county_fips"],
                    "r": cmap["counties"].get(m["county_fips"], {}).get("region") or nearest_region(m["lat"], m["lon"]), "x": x, "y": y,
                    "w": e.get("water", []), "h12": ws.get("huc12"), "h8": ws.get("huc8"), "gl": shore.get(m["geoid"])})
    out.sort(key=lambda p: (p["n"].lower(), p["c"]))
    return out


GOLF = r"golf|country club|\bC\.?C\.?\b|links"
USE_GROUPS = {"Irrigation": "Farm irrigation", "Community Water Supply": "Public water systems", "Public Water Supply": "Public water systems",
              "Public water supply": "Public water systems", "Industrial": "Industry", "Industrial/Manufacturing": "Industry",
              "Mining": "Mining and dewatering", "Dewatering": "Mining and dewatering", "Livestock": "Livestock", "Bottled Water": "Bottled water",
              "Power Generation": "Power plants"}


def egle_use_file():
    """The newest EGLE facility water-use file on disk (engine/data/raw/lit/egle_water_use_facility_YYYY.xlsx). EGLE's site refuses
    scripted downloads, so each year's file is downloaded by hand; `python -m engine.update --list` says when a newer year is due."""
    import glob
    files = sorted(glob.glob(os.path.join(RAW, "egle_water_use_facility_[0-9][0-9][0-9][0-9].xlsx")))
    if not files:
        raise FileNotFoundError("No EGLE water-use file in " + RAW + "; see docs/data-updates.md")
    return files[-1]


def county_uses():
    """EGLE 2025 reported withdrawals by facility, grouped by county into plain categories (million gallons a day, averaged over the year).
    Golf courses are irrigation facilities whose names mark them as golf or country clubs; anything not grouped is 'Other'."""
    df = pd.read_excel(egle_use_file(), sheet_name="Sheet1")
    df["County"] = df["County"].astype(str).str.strip().replace({"Saint Clair": "St. Clair", "St Clair": "St. Clair", "Saint Joseph": "St. Joseph", "St Joseph": "St. Joseph"})
    # Entries far outside the range of their kind are left out and reported (see methods). Irrigation: the largest entry
    # is ~9x the next-largest farm statewide, which reads as a reporting error rather than a real withdrawal.
    odd = (df["Purpose"] == "Irrigation") & (df["Total Gallons"] > 2e10)
    flags = {r["County"]: f"One {r['Purpose'].lower()} entry ({r['Facility']}) reports {r['Total Gallons'] / 1e9:,.1f} billion gallons for 2025, about {r['Total Gallons'] / 365 / 1e6:,.0f} million gallons a day. That is many times the largest similar entry elsewhere in Michigan, so it is left out here as a likely reporting error."
             for _, r in df[odd].iterrows()}
    df = df[~odd].copy()
    golf = (df["Purpose"] == "Irrigation") & df["Facility"].astype(str).str.contains(GOLF, case=False, regex=True)
    df["group"] = df["Purpose"].map(USE_GROUPS).fillna("Other")
    df.loc[golf, "group"] = "Golf courses"
    out, n_golf = {}, {}
    for (c, g), v in df.groupby(["County", "group"])["Total Gallons"].sum().items():
        if c and c != "nan":
            out.setdefault(c, {})[g] = round(float(v) / 365 / 1e6, 3)
    for c, n in df[golf & (df["Total Gallons"] > 0)].groupby("County").size().items():
        n_golf[c] = int(n)
    per = df.loc[golf & (df["Total Gallons"] > 0), "Total Gallons"] / 365
    stats = {"golf_courses_reporting": int(len(per)), "golf_median_gpd": round(float(per.median()), -2),
             "golf_p25_gpd": round(float(per.quantile(0.25)), -2), "golf_p75_gpd": round(float(per.quantile(0.75)), -2)}
    stats["flags"] = flags
    return out, n_golf, stats


GREAT_LAKE_BY_HUC4 = {"0401": "Lake Superior", "0402": "Lake Superior", "0418": "Lake Superior", "0403": "Lake Michigan", "0404": "Lake Michigan",
                      "0405": "Lake Michigan", "0406": "Lake Michigan", "0419": "Lake Michigan", "0407": "Lake Huron", "0408": "Lake Huron",
                      "0420": "Lake Huron", "0424": "Lake Huron", "0409": "Lake St. Clair and the Detroit River", "0410": "Lake Erie"}


WATER_SOURCES = {"attains2026", "mi_part22", "mdnr_trout", "noaa_cag", "echo", "cwns2022", "usgs_marquette", "mpca_emc", "nsqd", "stepl", "egle_ms4", "kcdc_rules",
                 "bmpdb2020", "semcog_lid", "epa_fact26", "epa_mm8", "part91", "mpca_salt", "egle_rule57", "cat3516c", "uptime2014", "amazon_mo2026",
                 "wyofile2025", "cfr112", "herb2007", "stefan2010", "rule75", "jea2024", "rule60", "egle_dc_faq", "wleb_dap", "nri2017", "simple_method",
                 "usgs_wbd", "epa_wsaw", "noaa_atlas14", "wellogic", "wwat", "mcl327"}


def build_waters():
    """site/waterledger/mi/data/waters.json: receiving-water impairments by HUC12 (with downstream links), sewer plants,
    county rainfall and the runoff water quality parameters. Public data only."""
    from waterledger_data import waters as wi
    from waterledger_models import runoff as rq
    h12 = wi.by_huc12()
    trout = wi.trout_by_huc12()
    for k, v in h12.items():
        v["gl"] = GREAT_LAKE_BY_HUC4.get(k[:4])
        if k in trout:
            v["tr"] = [trout[k]["n"], trout[k]["names"]]
    plants = []
    for p in wi.potws():
        x, y = proj(p["lon"], p["lat"])
        # ECHO's past-year average flow is kept only where it is plausible against the design flow (unit errors are common at lagoons)
        if p["flow_mgd"] and not (p["design_mgd"] and 0.1 <= p["flow_mgd"] / p["design_mgd"] <= 1.3):
            p["flow_mgd"] = None
        plants.append({"id": p["id"], "n": p["name"], "city": p["city"].lower(), "x": x, "y": y, "major": p["major"], "cso": p["cso"],
                       "lagoon": p["lagoon"], "flow": p["flow_mgd"], "design": p["design_mgd"], "recv": (p["receiving"] or "").title(), "h12": p["huc12"]})
    # household wells by place: [drift wells, drift depth ft, drift water level ft, rock wells, rock depth, rock water level] (EGLE Wellogic)
    wells, HW = {}, wi.household_wells()
    for p in json.load(open(OUT_PLACES))["places"]:
        w = HW.get((p["c"], wi.place_stem(p["n"])))
        if w:
            d, r = w.get("drift", {}), w.get("rock", {})
            wells[p["g"]] = [d.get("n", 0), d.get("depth"), d.get("swl"), r.get("n", 0), r.get("depth"), r.get("swl")]
    data = {"generated": datetime.date.today().isoformat(), "cycle": 2026, "groups": wi.LABELS, "wells": wells, "h12": h12, "plants": plants, "rain_in": wi.county_precip(), "runoff": rq.PARAMS,
            "sources": {k: {"citation": c, "url": u, "short": SHORT.get(k, k)} for k, (c, u) in SOURCES.items() if k in WATER_SOURCES}}
    with open(OUT_WATERS, "w") as f:
        json.dump(round_tree(data, 3), f, separators=(",", ":"))
    print("wrote", OUT_WATERS, os.path.getsize(OUT_WATERS), "bytes;", sum(1 for v in h12.values() if "i" in v), "HUC12s with listings;", len(plants), "plants")


def build_power():
    """site/waterledger/mi/data/power.json: the electric utilities serving each place (MPSC territories, with the share of the place each
    covers) and each utility's load (EIA-861: yearly Michigan retail sales as an average MW, and summer and winter peaks where reported),
    plus Michigan's total retail sales. Public data only."""
    from waterledger_data import power as pw
    T, L, year = pw.territories(), pw.utility_loads(), pw.eia_year()
    idx = {q["name"]: i for i, q in enumerate(T)}
    utils = []
    for q in T:
        e = L[pw.EIA_ID[q["name"]]]
        utils.append({"n": q["name"], "type": q["type"], "cust": e["customers"], "avg_mw": round(e["mwh"] / 8760, 1),
                      "summer_mw": e["summer_mw"], "winter_mw": e["winter_mw"]})
    bounds = json.load(open(os.path.join(RAW_PLACES, "boundaries.json")))
    by_place = {}
    for p in json.load(open(OUT_PLACES))["places"]:
        rings = bounds.get(p["g"])
        if rings:
            by_place[p["g"]] = [[idx[n], sh] for sh, n in pw.place_utilities(rings, T)]
    mi = pw.michigan_retail_mwh()
    data = {"generated": datetime.date.today().isoformat(), "eia_year": year, "michigan": {"mwh": round(mi), "avg_mw": round(mi / 8760)},
            "utilities": utils, "places": by_place,
            "sources": {k: {"citation": c, "url": u, "short": SHORT.get(k, k)} for k, (c, u) in SOURCES.items() if k in ("mpsc_territory", "eia861")}}
    with open(OUT_POWER, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    print("wrote", OUT_POWER, os.path.getsize(OUT_POWER), "bytes;", len(utils), "utilities;", sum(1 for v in by_place.values() if v), "places with a utility")


MORATORIA_CSV = setting("mi_moratoria_csv")        # the hand-kept list of Michigan moratoria (public sources)
OUT_MORATORIA = os.path.join(SITE, "data", "moratoria.json")


def build_moratoria():
    """site/waterledger/mi/data/moratoria.json: Michigan data center moratoria from public sources (docs/research/moratoria-michigan.csv),
    each placed on the map. Cities and townships match Water Ledger's places; villages use the Census point and take their water
    facts from the township around them; counties sit at the county's center."""
    import csv
    from waterledger_data import places as pl
    places = json.load(open(OUT_PLACES))["places"]
    counties = {c["name"]: c for c in pl.counties()}
    bounds = json.load(open(os.path.join(RAW_PLACES, "boundaries.json")))
    by = {(p["c"], p["n"].lower()): p for p in places}

    def villages():
        path = os.path.join(RAW_PLACES, "villages_mi.json")
        if not os.path.exists(path):
            d = pl._get("https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/Places_CouSub_ConCity_SubMCD/MapServer/4/query",
                        {"where": "STATE='26' AND LSADC='47'", "outFields": "BASENAME,GEOID,INTPTLAT,INTPTLON", "returnGeometry": "false", "resultRecordCount": 2000, "f": "json"})
            json.dump([f["attributes"] for f in d["features"]], open(path, "w"))
        return json.load(open(path))
    vill = villages()

    def township_at(lon, lat):
        for g, rings in bounds.items():
            if pl._inside(lon, lat, rings):
                return g
        return None

    out, missing = [], []
    for r in csv.DictReader(open(MORATORIA_CSV)):
        name, kind, county = r["name"].strip(), r["kind"].strip().lower(), r["county"].strip().replace(" County", "")
        rec = {k: (r.get(k) or "").strip() for k in ("name", "kind", "county", "action", "adopted", "length_months", "expires", "status", "proposal",
                                                       "source_title", "source_publisher", "source_date", "source_url", "verified", "notes")}
        rec["county"] = county
        g = x = y = None
        if kind in ("city", "township", "charter township"):
            stem = re.sub(r"^(city|village|charter township|township) of\s+", "", name, flags=re.I)
            stem = re.sub(r"\s+(charter township|township|city)$", "", stem, flags=re.I).strip().lower()
            for k in ([f"{stem} {kind}"] + ([f"{stem} charter township", f"{stem} township"] if "township" in kind else [f"{stem} city"])):
                if (county, k) in by:
                    p = by[(county, k)]; g, x, y = p["g"], p["x"], p["y"]
                    break
        elif kind == "village":
            stem = re.sub(r"^village of\s+", "", name, flags=re.I).replace(" Village", "").strip().lower()
            hits = [v for v in vill if v["BASENAME"].lower() == stem]
            for v in hits:
                lat, lon = float(v["INTPTLAT"]), float(v["INTPTLON"])
                c = counties.get(county)
                if c and not pl._inside(lon, lat, c["rings"]):
                    continue
                x, y = proj(lon, lat)
                g = township_at(lon, lat)
                rec["within"] = g
                break
        elif kind == "county" and county in counties:
            x, y = proj(counties[county]["lon"], counties[county]["lat"])
        if x is None:
            missing.append(f"{name} ({kind}, {county})")
        rec.update(g=g if kind != "village" else None, x=x, y=y)
        if kind == "village" and rec.get("within"):
            rec["g"] = rec["within"]   # water facts come from the township around the village
        out.append(rec)
    out.sort(key=lambda r: (r["county"], r["name"]))
    json.dump({"updated": datetime.date.today().isoformat(), "source": "Public sources listed on each entry; compiled by Water Ledger", "moratoria": out},
              open(OUT_MORATORIA, "w"), separators=(",", ":"))
    print("wrote", OUT_MORATORIA, len(out), "entries;", len(missing), "not placed:", missing[:20])


def round_tree(x, nd=5):
    if isinstance(x, dict):
        return {k: round_tree(v, nd) for k, v in x.items()}
    if isinstance(x, float):
        return round(x, nd)
    return x


def main(n=200):
    regions = {}
    for rid, r in REGIONS.items():
        cache = f"{r.get('cache', rid)}_1995_2024"
        t, T, RH = hourly_weather(r["lat"], r["lon"], "1995-01-01", "2024-12-31", cache)
        res = cw.run_location(t, T, RH, n=n, mw=100.0)
        regions[rid] = {"name": r["name"], "station": r["station"], "lat": r["lat"], "lon": r["lon"], "per_100mw": res}
        print("ran", rid)

    staff = cw.staff_runs(n)
    Dv = {"regions": regions, "staff": {"runs": staff}}
    from waterledger.scenario import flow, band
    s2 = lambda v: f"{(round(v) if v < 100 else round(v / 10 ** (math.floor(math.log10(v)) - 1)) * 10 ** (math.floor(math.log10(v)) - 1)):,.0f}"
    gal = lambda b: f"about {s2(b['mid'] * 1e6)} gal/day (likely {s2(b['lo'] * 1e6)} to {s2(b['hi'] * 1e6)})"
    util = regions["west"]["per_100mw"]["dry"]["utilization"]["p50"]
    w300 = flow(Dv, "west", "dry", "withdrawn_avg", 300)
    lkwh = w300["mid"] * 1e6 * 3.78541 / (300 * 1000 * util * 24)
    hyb = lambda key: flow(Dv, "west", "hybrid", key, 300)["mid"] * 1e6 / 300
    # Van Buren: 1 GW of DTE contract over three buildings, one open loop; computers = contract / top of each design's PUE range [A]
    it_t, it_d = 1000 / 3 / PUE_DESIGN["towers"]["hi"], 2000 / 3 / PUE_DESIGN["dry"]["hi"]
    st = cw.staff_q(staff, it_t + it_d)
    vb = {k: band(regions["southeast"]["per_100mw"]["towers"][f"withdrawn_{k}"], it_t / 100)["mid"] + band(regions["southeast"]["per_100mw"]["dry"][f"withdrawn_{k}"], it_d / 100)["mid"]
          + st["withdrawn"]["p50"] for k in ("avg", "peak_1in10")}
    saline_it = 1400 / PUE_DESIGN["dry"]["hi"]
    mx = lambda r: f"{r:.1f}".removesuffix(".0") if r < 10 else s2(r)          # a multiple, as on the page (WQ.mult)
    low, gb, sal, sw = (flow(Dv, "west", "dry", "withdrawn_avg", 300), flow(Dv, "west", "dry", "withdrawn_avg", 100),
                        flow(Dv, "southeast", "dry", "withdrawn_avg", saline_it), flow(Dv, "west", "dry", "withdrawn_avg", 320))
    l500 = flow(Dv, "west", "dry", "withdrawn_avg", 500)
    inside = lambda v, b: b["lo"] <= v <= b["hi"]
    not_counted = "landscape watering, humidification for designs that cool with outside air, and other site uses this page does not count"
    validation = [
        {"check": "Cooling towers, water use per IT kWh (makeup basis)", "published": "LBNL 2024 large tower-based facilities: median ~2.0–2.2 L/kWh, range ~1.75–2.75 (U.S. climates)",
         "ours": f"{regions['west']['per_100mw']['towers']['wue_makeup_l_per_kwh']['p10']:.2f}–{regions['west']['per_100mw']['towers']['wue_makeup_l_per_kwh']['p90']:.2f} L/kWh (West Michigan)",
         "reading": "Lower than the U.S. median, as expected for a cool climate; within the published range.", "sources": ["lbnl2024"]},
        {"check": "Hybrid / evaporative assist (consumed)", "published": "Lei et al. 2025, climate zone 5A: ~0.1 (efficient) to ~0.7 (inefficient) L/kWh; operators 0.1–0.3",
         "ours": f"{regions['west']['per_100mw']['hybrid']['wue_l_per_kwh']['p10']:.2f}–{regions['west']['per_100mw']['hybrid']['wue_l_per_kwh']['p90']:.2f} L/kWh",
         "reading": "At or just below the efficient end of the published range, as expected in a cold climate.", "sources": ["lei2025", "lbnl2024"]},
        {"check": "Closed loop, water taken per IT kWh", "published": "~0–0.1 L/kWh for designs that use no water for cooling (staff use, and humidification where outside air is used)",
         "ours": f"About {lkwh:.3f} L/kWh at 300 MW, West Michigan, staff water included",
         "reading": "Inside the range, near the bottom: these designs recirculate indoor air, so the humidification behind the top of LBNL's range is not counted. A weak check on its own; the Michigan figures below say more.", "sources": ["lbnl2024"]},
        {"check": "Observed utility data, Northern Virginia (per MW of facility power capacity)", "published": "Air-cooled ~150 gal/day/MW; mixed (~60–70% water-cooled) 800–1,006 average, 2,435–3,060 peak day; evaporative peak up to 8,500",
         "ours": f"Per MW of IT capacity at 300 MW, West Michigan: closed loop ~{w300['mid'] * 1e6 / 300:,.0f}; hybrid ~{hyb('withdrawn_avg'):,.0f} average and ~{hyb('withdrawn_peak_1in10'):,.0f} on a 1-in-10 peak day",
         "reading": f"Closed loop is far below the metered air-cooled figure: the Virginia sites are older, many cool with outside air, and metered totals include {not_counted}; ICPRB's per-MW basis is facility capacity, not computing capacity. Hybrid is the same order of magnitude as the mixed sites.", "sources": ["icprb2025", "icprb2026"]},
        {"check": "Google data center fleet, 2025", "published": "~0.94 L per kWh of facility electricity (10,523 million gallons over 42.4 TWh, all climates and designs)",
         "ours": "Between our hybrid and cooling-tower estimates, as expected for a mixed global fleet", "reading": "Consistent.", "sources": ["google2026"]},
        {"check": "Van Buren Township (Google; 1 GW DTE contract, three buildings, one open loop)", "published": "Developer estimate 2–3.6 MGD (township FAQ, Jan 2026)",
         "ours": f"About {vb['avg']:.1f} MGD average, {vb['peak_1in10']:.1f} MGD 1-in-10 peak (one building's third of the contract with cooling towers, about {it_t:,.0f} MW of computers; two-thirds closed loop, about {it_d:,.0f} MW; Southeast Michigan)",
         "reading": "Inside the developer's range." if 2.0 <= vb["avg"] <= 3.6 else "Outside the developer's range.", "sources": []},
        {"check": "Lowell Charter Township (Microsoft), closed loop", "published": "About 6,000 gal/day (2.2 million gallons a year) excluding cooling, a Microsoft projection reported locally; size not published; primary document not yet located",
         "ours": f"{gal(w300)} at 300 MW, the starting size; {gal(flow(Dv, 'west', 'dry', 'withdrawn_avg', 500))} at 500 MW",
         "reading": f"The reported figure is about {mx(0.006027 / low['mid'])} times ours at 300 MW, " + ("inside" if inside(0.006027, low) else "outside") + " our likely range there, and " + ("inside" if inside(0.006027, l500) else "outside") + " it at 500 MW. The campus's size is not published, and ours counts staff water and loop top-ups only.", "sources": ["lowell_firstlook"]},
        {"check": "Gaines Township (Microsoft), per building", "published": "About 2,000 gal/day per building (Microsoft at the April 15, 2026 hearing, as reported); building size and count not published",
         "ours": f"{gal(flow(Dv, 'west', 'dry', 'withdrawn_avg', 100))} for one 100 MW building",
         "reading": f"The reported figure is about {mx(0.002 / gb['mid'])} times our middle estimate, " + ("inside" if inside(0.002, gb) else "outside") + " our likely range.", "sources": ["gaines_sunnews"]},
        {"check": "Saline Township (Related Digital for Oracle and OpenAI; 1.4 GW DTE contract), closed loop", "published": "About 20,000 gal/day at the start of operations, a developer estimate as reported locally; primary document not yet located",
         "ours": f"{gal(flow(Dv, 'southeast', 'dry', 'withdrawn_avg', saline_it))} at full build-out, about {saline_it:,.0f} MW of computers",
         "reading": f"The reported figure is about {mx(0.02 / sal['mid'])} times ours and " + ("inside" if inside(0.02, sal) else "above") + " our likely range, although it is for the start of operations and ours is for the full campus. It may include uses this page does not count, such as landscape watering, process water or a phased first fill; the primary document has not been found.", "sources": ["saline_post"]},
        {"check": "Switch data center, Gaines Township (operating since 2017; metered, not projected)", "published": "About 10 million gallons in 2024, about 27,000 gal/day, as a township official reported; design 320 MW; actual load and cooling design not public",
         "ours": f"{gal(flow(Dv, 'west', 'dry', 'withdrawn_avg', 320))} for a closed loop at 320 MW and 60–90% load",
         "reading": f"Metered use is about {mx(0.0274 / sw['mid'])} times ours. Switch's cooling design and actual load are not public, and a metered total includes {not_counted}. Metered use at an operating site can run well above an applicant's projection.", "sources": ["wgvu_switch"]},
    ]
    print("VALIDATION"); [print(" ", v["check"], "|", v["ours"]) for v in validation]

    cnt = pl.counties()
    munis = pl.municipalities()
    bounds = pl.boundaries(cnt)
    enr = pl.enrich(munis, bounds)
    cmap = build_map(cnt)
    places = build_places(cnt, munis, enr, cmap, great_lake_near(bounds))
    storms = pl.county_design_storms(cnt)
    tracker_muni = {}
    for tid, (name, county) in TRACKER_MUNI.items():
        hit = [p["g"] for p in places if p["n"].lower() == name.lower() and p["c"] == county]
        tracker_muni[tid] = hit[0] if hit else None
    with open(OUT_PLACES, "w") as f:
        json.dump({"source": "Municipalities: U.S. Census TIGERweb county subdivisions; water systems: EPA Community Water System Service Area Boundaries (reported or modeled); watersheds: USGS Watershed Boundary Dataset", "places": places}, f, separators=(",", ":"))
    with open(OUT_MAP, "w") as f:
        json.dump(cmap, f, separators=(",", ":"))
    print("places", len(places), os.path.getsize(OUT_PLACES), "map", os.path.getsize(OUT_MAP), "tracker", tracker_muni)

    uses, n_golf, golf_stats = county_uses()
    lake_t = pd.read_csv(os.path.join(RAW, "glerl_lt_avg_temp.csv"), skiprows=[1])
    lake_src = {}
    for name, code in (("Lake Michigan", "m"), ("Lake Superior", "s"), ("Lake Huron", "h"), ("Lake Erie", "e"), ("Lake St. Clair", "e")):
        t = lake_t[lake_t["lake"] == code].sort_values("dayOfYear")["temperature"].values
        lake_src[name] = lc.run_lake(t, n=n)
    lake_src["note"] = "Lake St. Clair is not in the GLERL series; Lake Erie temperatures stand in for it."
    lake_src["ranges"] = {k: list(v) for k, v in lc.RANGES.items()}
    data = {
        "model_version": MODEL_VERSION,
        "generated": datetime.date.today().isoformat(),
        "units": "MGD = million gallons per day; per_100mw values are per 100 MW of IT capacity at the sampled utilization",
        "percentiles": "p10/p50/p90 over a Monte Carlo of the parameter ranges; central = all parameters at mid-range",
        "designs": cw.LABELS,
        "parameters": {k: {"range": list(v), "sources": PARAM_SOURCES.get(k, [])}
                       for k, v in list(cw.RANGES.items()) + [("topup", cw.TOPUP)] + [("staff_" + k, v) for k, v in cw.STAFF.items()]},
        "regions": regions,
        "staff": {"runs": staff, "note": "Staff water per run: [core people, people per MW of IT capacity, gallons per person a day, share used up]; "
                                         "added to the per_100mw results at the campus's size (scenario.flow, WQ.flow)"},
        "power": POWER,
        "pue_design": PUE_DESIGN,
        "power_supply": POWER_SUPPLY,
        "home_kwh_month": 618.2,
        "context": CONTEXT,
        "county_uses_mgd": uses,
        "lake_source": lake_src,
        "county_golf_courses": n_golf,
        "golf": golf_stats,
        "tracker_muni": tracker_muni,
        "county_storms_in": storms,
        "region_meta": {k: {"name": r["name"], "station": r["station"]} for k, r in REGIONS.items()},
        "validation": validation,
        "sources": {k: {"citation": c, "url": u, "short": SHORT.get(k, k)} for k, (c, u) in SOURCES.items()},
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(round_tree(data), f, separators=(",", ":"))
    print("wrote", OUT, os.path.getsize(OUT), "bytes")


if __name__ == "__main__":
    import sys
    {"waters": build_waters, "moratoria": build_moratoria, "power": build_power}.get((sys.argv[1:] or [""])[0], main)()
