# Adding a state: the package side

How a state gets into the waterledger packages and onto data.waterledger.org, as a process a runner can start and stop: each step
has a command, what it writes, a test that says it is done, and whether it needs Andrew's approval. The website side (site, trackers,
rules, deploy, and the runner `engine/add_state.py`, which calls the commands here) is a Northline document.

Checked against the code on Nov 5, 2026: 3.10.0 (model 1.8). The ERA5 path is the cells, the runs and the check below; the snapshot
(step 4) is format 3 and carries the cell results. Michigan, Ohio, Virginia and Texas are the only states built so far, so a fifth may turn up something new. Georgia, Wisconsin and Wyoming have had tracker footprints
only, with no build.

## What is automatic

Any state answers `wl.place()`, `place.context()` and `site.estimate()` from the national tier, with no state folder and no code
(design 0002). `waterledger.states.FIPS` lists every state.

| Layer | Source | Module |
|---|---|---|
| Places | Census TIGERweb: incorporated places, active townships, counties | `waterledger.national`, `waterledger_data.census` |
| Water systems | EPA service area boundaries, SDWIS | `waterledger_data.supply` |
| Sewer plants | EPA Clean Watersheds Needs Survey 2022, ECHO | `waterledger_data.wastewater` |
| Watersheds, impairments | USGS WBD, EPA ATTAINS, the watershed tracer | `waterledger_data.receiving`, `waterledger_data.trace` |
| Cooling weather (model 1.8) | ERA5 at each place's 0.25-degree cell, the nearest at least half land, 1995-2024; shore cells corrected toward stations near the shore (designs 0004, 0005) | `waterledger_data.era5`, `waterledger.national.era5`, `waterledger_models.quantile_mapping` |
| Cooling weather (model 1.7, the published snapshots) | NOAA ISD, one station per climate division | `waterledger_data.divisions`, `waterledger.national.climate` |
| Rainfall, road salt, golf | NOAA station records by climate division (both models) | `waterledger_data.divisions`, `waterledger.national.climate` |
| Design storms | NOAA Atlas 14 | `waterledger_data.divisions` |
| Electricity | HIFLD territories, EIA-861, plant reports | `waterledger_data.energy`, `waterledger_data.power` |
| County water use | USGS revised 2015 estimates | `waterledger_data.wateruse` |

A state folder (`states/<st>/`) replaces only the layers it does better. Only Michigan has one, and a new state doesn't need one.

## What can stop a state

Check these before starting; each is a decision for Andrew, not something a step works around.

- **Design storms: Atlas 14.** `divisions.design_storms` reads NOAA Atlas 14 and skips a county it can't read; the `design_storms`
  check then fails the build below 99%. Oregon and Washington are outside Atlas 14 (check NOAA's coverage map for any other state).
  Such a state needs another storm source first (design 0002, decision 5), and none is built.
- **Weather: outside the grid.** ERA5's land-sea mask ships for 24-50 N, 125-66 W (`waterledger_data/tables/era5_conus.npz`), the
  lower 48. Alaska and Hawaii are outside it: `waterledger era5 cells AK` stops with "outside the shipped grid". They'd need the mask
  for their own boxes, and a check of ERA5 there.
- **Weather: stations near the border.** Quantile mapping's stations are NOAA's (ISD) and Canada's (ECCC). There are no Mexican
  stations, so shore cells on the Gulf near Mexico, and any cell whose only near stations are in Mexico, are corrected from US
  stations or not at all.
- **Weather: the ERA5 check fails** (step 3). For example a mountain state, where land cells are off by more than the four states'
  worst. That is a method question (an elevation correction on land cells, say), not a step to repeat.
- **Rainfall.** A county with no NOAA record stops the build. An independent city with no record takes its surrounding county's
  (`national.climate.surrounding_county`), and the place's context says so.
- **Stations.** Rainfall, salt and golf still need a station per climate division with 85% of hours observed over 1995-2024; see
  `docs/methods/station-distance-check.md`.

## The steps

Run in order. A runner moves on when a step's done-test passes, and stops at a step that needs approval or a decision. Every step
resumes where it stopped if run again. `ST` is the state's two letters; `CACHE` is `WATERLEDGER_CACHE`, default `~/.cache/waterledger`.

### 0. Preflight

```bash
uv sync
uv run waterledger era5 cells ST --json
```

- **Writes:** nothing.
- **Done when:** the command exits 0. Its JSON gives `cells`, the number of ERA5 cells the state's places use. It exits non-zero if a
  place is outside the grid (Alaska, Hawaii). Before the state's first build the places come from Census, so this step fetches them.
- **Approval:** none. Check Atlas 14 coverage by hand (above); a state outside it stops here.

### 1. Build the state's layers

```bash
uv run waterledger build-state ST --out build-report --no-checks
```

Or on GitHub, one state at a time (NOAA's rate limit has stopped parallel builds; the job has a 300-minute limit):

```bash
gh workflow run build-state --ref main -f state=ST -f upload=false
```

- **Writes:** every layer to `CACHE` (places, supply, wastewater, receiving, model 1.7's division runs, storms and rain, energy,
  water use), and `build-report/ST_build.json` (counts, timings and sources' dates by stage).
- **Done when:** the command exits 0 and `build-report/ST_build.json` exists with a `stages` entry for each of `places`, `supply`,
  `wastewater`, `receiving`, `cooling`, `storms_and_rain`, `energy` and `wateruse`.
- **Approval:** none.

### 2. Run the ERA5 cells, in parts

One run per cell: 400 draws, about 40 s a cell over a long run at ten workers on Andrew's Mac (one per performance core; 31 s in short tests). Split the state into parts of about 205 cells (about 2.3 hours each),
`n = ceil(cells / 205)` parts, and start each by hand, an evening or overnight:

```bash
uv run waterledger era5 cells ST --part 1/n --json
WATERLEDGER_R2=wrangler uv run waterledger era5 run ST --part 1/n --workers 10
```

The second command is repeated for parts 2/n to n/n. Leave out `WATERLEDGER_R2=wrangler` (or pass `--no-r2`) to keep everything
local; with it, raw cells and results also go to the private bucket `waterledger-raw` as they are made, and a part can restart on
another machine (README, "Model 1.8's ERA5 runs").

- **Writes:** `CACHE/era5/raw/<cell>/<fetch date>.npz` and `.json` (the weather as fetched), `CACHE/era5/anchors/<station>.json` and
  `.npy` (the shore stations), and `CACHE/era5/runs/model1.8/<cell>.json`, one per cell, as each finishes.
- **Done when:** for a part, `era5 run` exits 0 and that part's `done` equals its `cells` in `era5 cells ST --part k/n --json`. For the
  state, `uv run waterledger era5 cells ST --json` prints `"complete": true`.
- **Approval:** none; Andrew starts the parts. Cells shared with a state already run are reused, not run again.

### 3. Check ERA5 against the state's stations

```bash
uv run waterledger era5 check ST --workers 10
```

Design 0005's leave-one-station-out check, as `docs/methods/qm-check/` ran it for the first four states. It needs no runs from step 2,
so a runner may take it first and stop early on a fail. Every qualifying station (ISD by one ID or linked, and ECCC) in the state or
within 100 km of its places is held out in turn, and its cell given the decided method. Up to 12 places, each the nearest within 30 km
of a station in the state, are run through the cooling model against the station's own record (24 runs, about 15 minutes at ten
workers, plus qualifying the stations the first time: Ohio's 54 candidates and its weather part took 12 minutes).

The criteria (`waterledger.national.era5_check.CRITERIA`) are the four accepted states' worst result plus a margin:

| | Test | Limit | Four states |
|---|---|---|---|
| W1 | land stations held out | at least 5 | |
| W2 | land cells, median absolute error in the 0.4% design dry-bulb | 0.75 C | 0.30-0.68 (Virginia) |
| W3 | land cells, absolute mean error in the design dry-bulb | 0.5 C | 0.07-0.33 (Texas) |
| W4 | land cells, median absolute error in the 0.4% wet bulb | 0.4 C | 0.10-0.25 |
| W5 | corrected shore cells (3 or more), median absolute error in the design dry-bulb | 0.5 C | 0.19-0.32 |
| W6 | corrected shore cells: no worse than uncorrected | | always better |
| P1 | places sampled | at least 5 | |
| P2 | places, median absolute difference in the hybrid average day | 8% | 1.9-4.6% (Virginia) |
| P3 | places, absolute mean difference in the hybrid average day | 6% | 0.6-4.9% (Virginia) |
| P4 | places, median absolute difference in the hybrid peak day | 6% | 0.5-3.2% (Virginia) |
| P5 | places, median absolute difference in towers' average day | 2% | 0.03-0.22% |

The four states' figures are from `docs/methods/qm-check/` (Nov 4, 2026). Each state's stations are those in it or within 100 km of
its places, held out under the decided rule; its places are the station check's within 30 km of their station (Michigan 1, Ohio 5,
Virginia 4, Texas 6). These are the first limits, set from four states; Andrew may change them, in `CRITERIA` and here.

- **Writes:** `CACHE/era5/check/ST/check.json` (every station's and place's errors, the criteria and the verdict) and `check.md` (the
  same tables as design 0005). `--out DIR` writes them elsewhere.
- **Done when:** exit code 0 (pass). Exit 1 is a fail: the report says which criterion and by how much, and the state stops for
  Andrew. `--weather-only` skips the places and can't pass.
- **Approval:** a fail needs Andrew's decision on the method. The command never changes the method.

### 4. Write and check the snapshot

```bash
uv run waterledger snapshot ST --out snapshot
uv run waterledger check-snapshot ST --dir snapshot
```

- **Writes:** `snapshot/ST/<date>/`, format 3 (places, supply, wastewater, receiving, climate, energy, water use, `manifest.json` with every file's
  sha256), and the checks' results into its `manifest.json`.
- **Done when:** `check-snapshot` exits 0. It exits non-zero when a layer covers less of the state's places than `COVERAGE_MIN`, or any
  of the 50 sampled places fails `place.context()` or `site.estimate()`:

| Check | Least share of places |
|---|---|
| Watersheds | 99% |
| Utilities | 95% |
| Climate division | 99% |
| Sewer plant within 40 km | 50% |
| County water use | 99% |
| Rainfall | 99% |
| Design storms | 99% |

  The end-to-end test runs for any state: `WATERLEDGER_TEST_STATE=ST WATERLEDGER_DATA=live uv run pytest -m live tests/test_state_end_to_end.py`
  (exit 0). The `build-state` workflow runs it too.
- **Approval:** none, but the checks by hand below come before publishing.

Then check the numbers by hand, since passing coverage doesn't mean a number is right:

1. Open the build report and compare the counts with what you know about the state.
2. Pick three places you can reason about. Confirm the main water system, the nearest sewer plant, the utility and the downstream path.
3. Compare 300 MW with cooling towers against a state already published. Towers should change little from place to place.
4. Read `check.md` from step 3: the stations furthest off, and the places, against what you know of the state's climate.

### 5. Publish

```bash
gh workflow run build-state --ref main -f state=ST -f upload=true
```

- **Writes:** `data.waterledger.org/ST/<date>/` and `ST/latest.json`. A published snapshot never changes; publishing the same date again
  stops, and needs `-f snapshot_id=<date>.2`.
- **Before it:** the workflow reads the cell results from R2. Runs made with R2 off go up by running each part again with
  `WATERLEDGER_R2=wrangler`; done cells are uploaded, not rerun.
- **Done when:** `https://data.waterledger.org/ST/latest.json` has `current` equal to the snapshot's date.
- **Approval:** **Andrew's, every time.** Nothing is published without it.

## For the runner: steps and their done-tests

| Step | Command | Done when | Stops for |
|---|---|---|---|
| 0 Preflight | `waterledger era5 cells ST --json` | exit 0 | Atlas 14 coverage (by hand); outside the grid |
| 1 Build | `waterledger build-state ST --out build-report --no-checks` | exit 0; `build-report/ST_build.json` has all eight stages | a build error |
| 2 Runs | `waterledger era5 run ST --part k/n --workers 10`, k = 1..n | `waterledger era5 cells ST --json` prints `"complete": true` | Andrew starts each part |
| 3 ERA5 check | `waterledger era5 check ST` | exit 0; `CACHE/era5/check/ST/check.json` has `"verdict": "pass"`, or Andrew accepts a fail (stated on the methods page) | a fail: Andrew decides the method |
| 4 Snapshot | `waterledger snapshot ST --out snapshot` (format 3, with the cells), then `waterledger check-snapshot ST --dir snapshot` | exit 0; the manifest has `checks` | a coverage or sample failure; the checks by hand |
| 5 Publish | `gh workflow run build-state ... -f upload=true` | `latest.json`'s `current` is the date | **Andrew's approval** |

## Optional state layers

These improve a state but aren't needed for a snapshot:

- **The state's own county water use.** Add a reader to `STATE_LAYERS` in `waterledger_data/wateruse.py`, add its downloaded file to
  `inputs()`, and write up the source in `docs/methods/water-use-sources.md`.
- **Golf course water.** Add the state to `GOLF` in the same file, with sources and a note. Without it, the comparison stays off.

## Code to change

These files name states by hand:

| File | What to add |
|---|---|
| `tests/conftest.py` | `STATES`, `POINTS` and `BY_NAME`, which tag tests with `state_<st>` markers |
| `docs/methods/build_briefs.py` | `NAMES`, `EXAMPLES`, `AGENCIES` (the state's ATTAINS organization) and the default list near the end of the file |
| `tests/test_national_*.py` | At least one known place for the state, with the facts you checked by hand |
| `README.md` | A row in the states table, before the release |

The `build-state` workflow takes any state; it no longer keeps a list.

## What to record

Record decisions twice, short and long:

- **Long:** a dated section in `docs/methods/national-tier-notes.md`: the stations chosen and any compromises, place, cell and plant
  counts, the ATTAINS cycle, the ERA5 check's verdict and anything it showed, and anything unusual about how the state is organized.
  Decisions that affect every state also go in `docs/methods/methods-log.md`.
- **The ERA5 check:** `check.md` from step 3, copied to `docs/methods/era5-checks/<st>.md` with the date.
- **Short:** the two-page brief, written by `docs/methods/build_briefs.py` to `docs/methods/<st>.pdf`.

An error found in one state is checked and fixed in every state.

## Not built yet

These are package requirements for every state, not only new ones.

| Item | What it is | What it would take |
|---|---|---|
| Station correction on land cells | Quantile mapping toward nearby stations on land cells, as on shore cells (decided Nov 6, 2026; methods log) | A new model version: the held-out check in all five states, new snapshots, parity, a release |
| ERA5 from CDS | Copernicus's own time series, 0004's named source | An ECMWF key (Andrew's); the open copy is what's built |
| ERA5 outside the lower 48 | Alaska and Hawaii | The mask for their boxes, and the check there |
| Storm source outside Atlas 14 | Older NOAA studies for states Atlas 14 doesn't cover | A reader for each study, plus coverage checks |
| Water source tag | Each water system marked as Great Lake, stream or groundwater, with [A] where inferred | Read source type from SDWIS and add a Great Lake check; a new field in `supply.json` and `Context` |
| Low-flow statistics | 7Q10 or similar along each place's downstream path | A national source, such as the National Water Model retrospective, checked against USGS gauges |
| Return-flow location | The sewer plant's discharge point and receiving water carried through to the site | Plants already have a point and receiving water; connect them to `Site` |
| Assessed status in snapshots | Whether each watershed was assessed | `receiving.by_huc12` already reads it as `a`, but `snapshot._downstream` drops it |
| `waterledger new-state` | A template command for a state folder (designs 0001 and 0002) | Not needed unless a state needs its own folder |
