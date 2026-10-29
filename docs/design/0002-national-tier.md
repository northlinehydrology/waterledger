# 0002: The national tier

Status: **agreed, Oct 29, 2026.** It builds on [0001](0001-schema-and-api.md) and ships in 2.x releases (adding states is a
feature, not a breaking change).

## Goal

Every state answers `wl.place(...)`, `place.context()` and `site.estimate()` from federal data. A state folder
(`states/<st>/`) replaces only the layers it does better, as Michigan does today. Ohio, Virginia and Texas are the
states the national tier is tested on, end to end:

- Ohio: a Great Lakes state with townships;
- Virginia: the largest data center market, with counties governing unincorporated land;
- Texas: a large state with its own Atlas 14 volume.

## Decisions

1. **A national provider** answers for any state. The registry uses a state's own provider where one exists, and each
   layer falls back to the national one.
2. **Geospatial libraries are standard.** geopandas and shapely are dependencies of `waterledger-data`, which needs
   spatial joins at national scale (about 38,000 places). `waterledger-models` stays numpy-only. matplotlib is dropped
   once Michigan's point-in-polygon code moves to shapely.
3. **Places:** cities, towns and villages everywhere; townships where they are governments; every county, for
   unincorporated land (design 0001, decision 6).
4. **Climate:** NOAA ISD station records, about one station per NOAA climate division, with the cooling Monte Carlo run
   at each station. Michigan stays on ERA5 (0001, decision 5).
5. **Design storms:** NOAA Atlas 14 by county. Older NOAA studies fill states Atlas 14 doesn't cover, when needed; Ohio,
   Virginia and Texas are all covered.
6. **County water use (USGS):** an optional comparison layer (how a facility compares with farms, industry and power
   plants in the county), labeled with its year. The estimate and impacts don't depend on it, and a state's reported
   data replaces it.
7. **Rules:** federal only at the national tier. State rules arrive as per-state rules files, and until then the
   national tier says "state rules not yet reviewed".

## Build order (each a commit or a few; released as 2.x minor versions)

1. National provider and registry fallback; geo dependencies; Michigan's point-in-polygon on shapely (outputs unchanged).
2. Places for any state (Census), with boundaries.
3. Supply (EPA service areas), wastewater (ECHO and CWNS), receiving waters (WBD and ATTAINS), all by state.
4. Climate: ISD stations by climate division, the cooling runs, Atlas 14 storms and county rainfall.
5. Energy (national utility territories, EIA-861, each state's generation mix) and the USGS county water-use layer.
6. Generic estimate logic. Michigan specifics (septic thresholds, Part 327, Great Lakes lake-source) move to states/mi.
7. The site format schema, `waterledger new-state`, the "adding a state" guide, nightly checks for the new sources, and
   end-to-end tests for Ohio, Virginia and Texas.
