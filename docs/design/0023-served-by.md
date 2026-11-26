# 0023: Which plant treats a place's sewage, and where its water comes from: who serves whom, not distance

Status: **built, Nov 25, 2026** (Andrew: "fix ... design 0023"), for 3.29.0. The rule as built and its measurement are in "As built" below; every change, place by place, is in `0023-changes.csv`.

## Why

A Water Review's cover names the water system and sewer plant that would serve a site, and the defaults behind every estimate (public
water or wells, sewer or septic) follow from them. Today both are guessed from geometry:

- **Sewer** (`wastewater.rank`, shared by every state): the place's own plant (named for it), else the plant named for the town whose
  water system serves the place, else the nearest plant of 0.5 MGD or more within 40 km.
- **Defaults** (`provider.default_wastewater`, `default_source`): sewer if a water system is mapped on 5% of the place or the first plant
  is within 10 km; public water likewise.

Andrew (Nov 25): a wrong plant or a wrong default "looks pretty stupid" on a report. The guesses that prompted this: Ada Township to
Lowell STP (Ada's sewers go to Grand Rapids), Loudoun County to Purcellville, Plymouth Township to Hamburg Township's plant, North
Muskegon to Grand Valley State's campus plant, and 12 Michigan places whose defaults flipped when a distance moved a few hundred metres
across the 10 km line (design 0011, step 6).

## The source: EPA's Clean Watersheds Needs Survey 2022

The survey the package already reads for plants also records how sewers connect. Each collection system is a facility of its own
(`FACILITY_TYPES`: "Collection: Separate Sewers", "Collection: Combined Sewers"), and `DISCHARGES` says where its flow goes, with a
percentage, to another facility, ending at a treatment plant. `AREAS_COUNTY` lists the counties each facility serves, and
`POPULATION_WASTEWATER` the people. These are the states' own reports to EPA.

Examples:

- Ada's two collection systems, "ADA SEWAGE DISPOSAL SYSTE" and "ADA TWP COLLECTION SEWERS", discharge 100% to Grand Rapids WWTP.
- Ypsilanti's go to YCUA.
- Van Buren Township's north system goes to the Northeast Huron Valley/Rouge Valley interceptor, its south system to Wyandotte WWTP.

## Measured, Nov 25 (`0011-measure/served_by.py`)

A place's collection systems are those named for it within its county, or located inside it. Each one's discharge chain is followed to
its plant(s), weighted by population served.

| State | Places | With a collection system | By name | Today's guess agrees |
|---|---|---|---|---|
| MI | 1,541 | 637 | 123 | 376 (59%) |
| OH | 2,318 | 1,414 | 420 | 815 (58%) |
| VA | 322 | 241 | 130 | 172 (71%) |
| TX | 1,481 | 895 | 131 | 579 (65%) |
| WI | 1,922 | 969 | 547 | 684 (71%) |
| IN | 1,661 | 934 | 310 | 583 (62%) |
| MN | 2,719 | 954 | 461 | 642 (67%) |
| PA | 2,621 | 272 | 102 | 176 (65%) |
| GA | 697 | 406 | 219 | 285 (70%) |
| IL | 2,807 | 1,475 | 436 | 1,011 (69%) |
| NY | 1,584 | 1,017 | 526 | 672 (66%) |
| AZ | 107 | 84 | 40 | 44 (52%) |

So about 9,300 places have survey evidence, and at about 3,000 of them today's guess names a different plant. The plant at the end of the
chain is on the snapshot's plant list 97% of the time; 27 chains end nowhere.

A sample of 14 Michigan disagreements matched by location only:

- 11 are better by the survey: Center Line, Hazel Park and Madison Heights to GLWA, not Warren; Plymouth Township to GLWA, not Hamburg;
  North Muskegon to Muskegon County Metro, not Grand Valley State; Allen Park to Wyandotte (Downriver); Putnam Township to Pinckney's
  plant; Boston Township to Saranac's and Clarksville's; Lyons Township to Muir-Lyons.
- 2 are a village's system inside a township (Emerson to Ithaca, Pipestone to Eau Claire). That's where a campus in the township could
  connect, but it should say so.
- 1 is wrong: Williamstown Township picks up Meridian Township's system, whose recorded location falls inside it.

**One conflict for Andrew.** The survey sends Gaines Township's collection sewers (Kent County) to Grand Rapids WWTP. Northline's Gaines
record (`engine/sites/gaines.toml`) has the Wyoming Clean Water Plant, from local sources. Either the survey is stale, or the township
uses both. Conflicts are listed, not resolved: the cover shows the survey's answer with its source, and a hand-kept site record wins in a
review.

## The rule proposed

**Sewer plant, in order, each labeled with its basis:**

1. **"survey, by name":** the plant(s) at the end of the place's own collection systems, named for it within its county, weighted by
   population served.
2. **"survey, in the place":** collection systems located inside the place (a village's inside a township). The cover says "a system in
   the place" and names it.
3. **"named for the place":** the place's own plant, as today.
4. **"the water system's town":** as today.
5. **"nearest":** within 40 km, as today, labeled as a guess by distance.

**Counties** (Virginia's, Georgia's): the survey's facilities whose primary county it is, the plant serving the most people.

**Defaults:**

- A place with survey evidence of a collection system defaults to the sewer whatever the distance.
- A place whose collection systems the survey lists as discharging nowhere (on-site only) defaults to septic or its own discharge.
- The 10 km line stays only where the survey says nothing, and the estimate says which basis was used.

**Water source** (second part, measured before it's built): EPA SDWIS lists consecutive connections, a water system that buys from
another (`SELLER_PWSID`). A place's water system then has a chain to its source system, and the sewer rule's step 4 can use the seller's
town (Ada Township's water comes from Grand Rapids). The 5% mapped-system line and the 10 km line get the same treatment as the sewer's.

**Every guess carries its basis** (`SewerPlant.basis`, `Supply.basis`), and the report cover prints it. A hydrologist confirms each one
before a handout goes out.

## As built (Nov 25, 2026)

Rules as built (`wastewater.served_by`, `wastewater.ranked_for`, `supply.sellers`):

- **A place's sewer systems** are the survey's collection systems:
  - those named for it, where its name is followed by a sewer or plant word or nothing ("ADA SEWAGE DISPOSAL SYSTE", "Scottsville (V)
    Sewers"; not "BENTON HARBOR-ST JOSEPH" for Benton) and the system lies within 15 km of the place;
  - those located inside it, unless named for another place (Meridian Township's system inside Williamstown Township is Meridian's).

  The survey seldom gives a collection system's county, so distance stands in.
- **All of a place's systems count together,** each weighted by the people it serves, and each is followed through DISCHARGES to its
  plants. This settled the Gaines conflict in the site record's favour: Cutlerville's system, inside the township, sends 81% of the
  flow to Wyoming; the township's own system sends 19% to Grand Rapids.
- **A county** with neither takes the survey's facilities whose primary county it is.
- **A survey link to a plant beyond 80 km is taken as a record error [A].** Examples: Benton Harbor-St. Joseph's location in the survey,
  424 km from Benton Township; Sugarcreek, Ohio's chain to Greene County's Sugarcreek plant, 228 km. GLWA's farthest served suburbs are
  56 km from Detroit's plant.
- **The town step** of the old rule takes the water system's seller's town too: SDWIS consecutive connections (Ada Township buys from
  Grand Rapids).
- **Every plant carries its basis:** "name", "inside", "county", "own", "system" or "nearest". A plant the survey reaches is in reach
  for the sewer default whatever the distance.

Measured on the twelve states' places (the 3.28 rule against 0023's, the same plant list):

| State | Places | Survey evidence | First plant changes | Sewer comes into reach |
|---|---|---|---|---|
| MI | 1,541 | 705 | 250 | 123 |
| OH | 2,318 | 1,219 | 419 | 84 |
| VA | 322 | 247 | 74 | 36 |
| TX | 1,481 | 1,086 | 338 | 50 |
| WI | 1,922 | 1,008 | 268 | 155 |
| IN | 1,661 | 736 | 220 | 77 |
| MN | 2,719 | 984 | 170 | 80 |
| PA | 2,622 | 242 | 75 | 12 |
| GA | 697 | 397 | 129 | 33 |
| IL | 2,807 | 1,388 | 339 | 37 |
| NY | 1,584 | 954 | 324 | 92 |
| AZ | 107 | 90 | 38 | 14 |

In all, there is survey evidence at 9,056 of 19,781 places. The first plant changes at 2,644: 1,152 by a system named for the place,
1,348 by a system inside it, 94 by county, 50 by the water seller's town. The sewer comes into reach at 793 places and goes out of
reach at none. The farthest survey-chosen plant is 78 km away.

**Water source.** The 5% line for a system serving a place stays. The 10 km line for extending a sizable system to a place with none
also stays: the survey's sewer evidence has no counterpart for water service areas beyond EPA's own maps. Each system now lists whom it
buys from (`WaterSystem.buys_from`).

## Checks before release

- The rule's answer against every hand-kept site record and case (Gaines, Cascade, Haring and the tracker's reviewed projects), every
  difference listed.
- Place by place in every state: which places change plant or default, and why. Andrew reads the list (no better estimate lost; fix all
  states).
- The page and the package agree (`check_parity`, every state).

## Decisions (agreed by building, Andrew, Nov 25, 2026)

1. CWNS collection systems and discharges come first, by name, then by location, then today's rules, each labeled with its basis.
2. Survey evidence overrides the 10 km and 5% lines for the defaults.
3. Counties use the survey's served-county table.
4. Water: SDWIS seller chains, measured next, built in the same release.
5. Gaines: Andrew says which plant is right, and whether the survey or the site record should be marked.
