# 0023: Which plant treats a place's sewage, and where its water comes from: who serves whom, not distance

Status: **proposed, Nov 25, 2026, for Andrew's agreement.** Measured; no code yet.

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

## Checks before release

- The rule's answer against every hand-kept site record and case (Gaines, Cascade, Haring and the tracker's reviewed projects), every
  difference listed.
- Place by place in every state: which places change plant or default, and why. Andrew reads the list (no better estimate lost; fix all
  states).
- The page and the package agree (`check_parity`, every state).

## Decisions to agree

1. CWNS collection systems and discharges come first, by name, then by location, then today's rules, each labeled with its basis.
2. Survey evidence overrides the 10 km and 5% lines for the defaults.
3. Counties use the survey's served-county table.
4. Water: SDWIS seller chains, measured next, built in the same release.
5. Gaines: Andrew says which plant is right, and whether the survey or the site record should be marked.
