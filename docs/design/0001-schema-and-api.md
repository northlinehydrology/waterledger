# 0001: Water Ledger schema and API (proposal)

Status: **proposal, for agreement before building the national version.** Oct 29, 2026.

## Why

Water Ledger works today, but its interfaces grew out of one website for one state:

- functions return loose dicts;
- the scenario reads the Michigan site's JSON files;
- the builder is one Michigan module;
- the ingest functions are Michigan-only and named for how they were built (`municipalities()`, `potws()`), not for what
  a user asks.

Going national, then state by state, with these interfaces would mean breaking users with every change.

The rule from now on: **a calculator change goes into the packages first, and waterledger.org follows.** So the
packages need a stable shape that a national layer, state layers and new facility types can grow inside, under major
versions.

## The shape

Five nouns, each a typed object with a JSON form:

| Object | What it is | Identified by |
|---|---|---|
| `Place` | where: a state, county, city, township or point | Census GEOID (or lat/lon) |
| `Context` | the public water facts around a place, in categories of layers | the place, plus a dated source for each layer |
| `Facility` | what is proposed: a data center now, other large users later | a type and its inputs (size, cooling design) |
| `Site` | a facility at a place, with its choices (source, wastewater, land) | place + facility + choices |
| `Estimate` | what the model says: water taken, used up, returned; impacts | the site, model version, data date |

```python
import waterledger as wl

place = wl.place("Gaines charter township, MI")        # or wl.place(geoid="2608131240"), wl.place(lat=42.86, lon=-85.6)
ctx = place.context()                                 # water systems, watershed and impaired waters downstream, sewer
                                                      # plants, design storms, climate, electric utility, state rules
site = wl.Site(place, wl.DataCenter(it_mw=300, cooling="hybrid"), acres=200, land_before="farm")
est = site.estimate()                                 # Estimate: est.water.withdrawn.avg -> Range(p10, p50, p90)
est.impacts()                                         # share of the water system's capacity, sewer headroom, runoff and
                                                      # loads before and after, electricity and its water
est.to_dict(); est.to_xarray()                        # JSON for websites, xarray for analysis
```

The current low-level modules stay underneath and keep working: `waterledger_models.datacenter.*` and
`waterledger_data.*`. The new objects are the front door.

A **Place** is any area or point Water Ledger can describe: a state, county, city, township, or a latitude and longitude.
This is broader than the Census Bureau's "place" (which leaves out townships and counties). A **Site** is a proposed
facility at a place.

## Context categories

The context is split by the question people ask. Each category is its own typed object with its own schema, providers
and change history, and it loads only when asked for:

| Category | Question | Layers |
|---|---|---|
| `jurisdiction` | who decides, under what rules | city or township, county, state; state and federal rules; moratoria and proposals on record |
| `supply` | where the water comes from | public water systems and their wholesale chain; reported water use nearby; groundwater and wells |
| `wastewater` | where used water goes | sewer plants (design capacity, current flow); discharge permits |
| `receiving` | what is downstream | watershed and downstream path; impaired waters and TMDLs; coldwater streams; later gauges and low flows |
| `climate` | the weather behind demand and runoff | weather station or region; rainfall normals; design storms |
| `energy` | the power behind the facility | electric utility territory and load; the water used to generate it |
| `land` (later) | the ground the site sits on | land cover, soils, wetlands, floodplain |

```python
ctx = place.context()
ctx.supply.systems
ctx.receiving.impaired_downstream
ctx.climate.storms
ctx.jurisdiction.rules
```

The categories line up with the impacts: a supply impact reads `supply`, a stream impact reads `receiving`, and so on.
They also follow the way Northline frames a site: approving jurisdiction, then the water system chain, then the
watershed or aquifer.

## National and state layers

A context is a stack of layers. Each layer has one schema and one or more providers:

- a **national provider**, which works in every state from federal data;
- optional **state providers**, which replace it where a state publishes better data.

| Layer | National provider | Example state provider |
|---|---|---|
| `places` | Census incorporated places and county subdivisions | (none needed) |
| `water_systems` | EPA service areas + SDWIS | |
| `watershed` | USGS WBD HUC12 + downstream links | |
| `impaired_waters` | EPA ATTAINS | |
| `sewer_plants` | EPA ECHO + CWNS | |
| `design_storms` | NOAA Atlas 14 | |
| `climate` | NOAA ISD stations by climate division | MI: ERA5 at eight hand-picked regions |
| `water_use` | USGS water use by county | MI: EGLE reported withdrawals |
| `electric_utility` | HIFLD territories + EIA-861 | MI: MPSC territories |
| `wells` | (none) | MI: EGLE Wellogic |
| `coldwater_streams` | (none) | MI: DNR trout streams |
| `rules` | federal (40 CFR 112, 125.81) | MI: Part 327, Part 22, Part 91, Rule 57 ... |

- **Provenance:** every layer value carries its source id, retrieval date and whether it came from the national or a
  state provider. The methods pages then say which source each state uses.
- **Rules are data, not code:** one TOML file per state (thresholds, citations), so adding a state's rules is reviewable
  text.

## Facility types

`Facility` is a small protocol: inputs, `water_use(climate) -> WaterUse`, `electricity()`, and `land()`. `DataCenter`
is the first type, built on today's cooling model. Battery plants, chip fabs, food processing and hydrogen can be added
later without changing `Site` or `Estimate`.

## Data products: the site format

`waterledger build <state>` writes a versioned site format: JSON files with a published JSON Schema. waterledger.org
reads that format; the website never imports Python.

- The national tier and each state tier are built the same way into `<site>/<state>/data/`.
- Michigan keeps its deeper files.

## Versions

Three numbers, kept apart, each with one meaning:

| Version | Where | Bumped when |
|---|---|---|
| Package (semver) | each package | the API changes: major = breaking, minor = new features, patch = fixes |
| Model version | `MODEL_VERSION` | the numbers change (methods, parameters, data); listed in the changelog |
| Site format | `SITE_FORMAT` in the JSON | the JSON files' structure changes |

This corrects a choice from the first releases. The models package version started with the model version (1.2.x),
which ties API changes to number changes. Proposal: from 2.0.0, package versions follow semver alone, and
`MODEL_VERSION` stays separate. The new API ships as **2.0.0** for all three packages, so everything under this
design is one major version.

## BMI

Anything that steps through time is a CSDMS BMI 2.0 component with CSDMS Standard Names. Lookups and results (Place,
Context, Estimate) are not; they connect to BMI instead.

- **Every Facility type ships a BMI component.** The data center has `CoolingWaterBmi` and `LakeCoolingBmi` today.
- **Sites configure it:** `site.to_bmi_config()` writes the component's config, with Context supplying the weather
  forcing and the facility's settings.
- **CI proves compliance:** CSDMS's `bmi-tester` runs on every component in CI, so compliance is tested, not claimed.

## Coupling (idea 3)

A `WaterUsersBmi` component (later, in `waterledger-nextgen`) takes a list of Sites and reports each one's withdrawal and
return through time at its stream location (a NextGen hydrofabric catchment). With `Site` and `Estimate` defined, this is
a thin layer on top, not a separate system.

## Decisions to agree

1. ~~The five objects~~ **Agreed (Oct 29):** Place, Context, Facility, Site, Estimate; Place defined broadly (above);
   Context split into the seven categories above.
2. **Layers:** national providers with state overrides, provenance on every value, and rules as per-state TOML.
3. **Validation:** pydantic in `waterledger` only. It validates inputs with clear errors, reads and writes JSON, and
   generates the site format's JSON Schema from the code. The models stay numpy-only for coupling frameworks and HPC,
   where a small install matters and validation belongs at the front door, not inside the physics.
4. **Versions:** decouple package semver from `MODEL_VERSION`; ship the new API as 2.0.0.
5. **National weather source:** NOAA ISD stations (observed, free, every state) for the national tier; Michigan keeps
   ERA5 until a model change is reviewed.
6. **Places nationally:** cities, towns and villages (incorporated places) in every state; townships and towns (county
   subdivisions) in the roughly 20 states where they are local governments; and every county, standing for the
   unincorporated land it governs (Connecticut's planning regions and Rhode Island's counties, which have no county
   government, are geographic units only). Every point in the country then falls inside a place that decides.
7. **BMI:** every Facility type ships a BMI 2.0 component; `site.to_bmi_config()`; `bmi-tester` in CI; the NextGen
   water-users component is BMI too.
