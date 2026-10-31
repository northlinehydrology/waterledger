# 0003: Data releases, and building locally when they can't be reached

Status: **agreed, Oct 29, 2026.** It builds on [0001](0001-schema-and-api.md) and [0002](0002-national-tier.md).

## The problem

The national tier assembles each state's data from public services: Census places, EPA water systems and sewer plants,
USGS watersheds and EPA impairments, NOAA station records, design storms and rainfall, utility territories. It also
runs the cooling model at each climate division's station. Doing that on a user's machine on first use is slow (about
15 to 20 minutes for three states), fragile (one federal service down breaks it), and not reproducible (two users a
week apart can get different answers).

## Decisions

1. **Hosted, versioned snapshots are the default.**
   - A scheduled GitHub Actions workflow builds each state's data in its own job (monthly, and on demand).
   - Each job checks its snapshot (schema, counts, the state's tests) and publishes it to Cloudflare R2 at
     `data.waterledger.org`, with a manifest of what is current.
   - Snapshots are dated and immutable. The package downloads the snapshot for the state asked about, caches it, and
     every Estimate records the data date it used.
   - Michigan's published files (waterledger.org/mi/data) are the first instance of this pattern.
2. **Building locally is the fallback, so the package keeps working even if the hosted data never comes back.** If the
   snapshot can't be reached (the site is down, a network error, or a state not yet published), the package offers to
   build the state locally from the public sources:

       Water Ledger's data for OH isn't reachable (data.waterledger.org: connection timed out).
       Build it locally from the public sources instead? This takes about 15 minutes the first time
       and is saved for later. [y/N]

   - Behavior is selectable: `fallback="ask"` (the default when someone is at the keyboard), `"build"`, or `"fail"`
     (the default in scripts and CI), or the environment variable `WATERLEDGER_FALLBACK`.
3. **The local build reports progress**, one bar per stage with counts and time remaining (tqdm):

       OH places       ████████████ 3/3 layers
       OH climate      ██████▌      6/10 divisions   ~3 min left
4. **The local build resumes.**
   - Every unit of work is saved as it finishes: a layer, a station-year of weather, a county's storms or rainfall, a
     division's cooling run.
   - A stopped or failed build continues where it left off when it runs again; nothing finished is fetched or computed
     twice.
5. **Failures degrade gracefully.**
   - Retries with backoff on timeouts and server errors.
   - If a service stays down, the build finishes every other layer, says plainly which one is missing and why, and
     lets the context come back with that category empty (None) rather than failing outright. The estimate needs only
     the place and climate.
   - The next run picks up the missing layer.
   - Nothing partial is ever published as a snapshot.
6. **Versions stay separate.** Code (package semver), numbers (`MODEL_VERSION`) and data (the snapshot date) each move
   on their own. Pinning `data="2026-11-01"` reproduces an old result.
7. **Some inputs stay manual.** Inputs a person maintains are shipped with the state's package code (`states/<state>/inputs/`), which the build jobs
   read: Michigan's EGLE water-use file (the site refuses scripted downloads), with facility names removed (changed from
   an inputs area of R2, Oct 30, 2026). The proposal and moratorium trackers are not
   part of the snapshots: they are a Northline service behind waterledger.org.

8. **Michigan moves to the same snapshot format (agreed Oct 29, 2026).** Every state then looks alike to the package and
   the site. It moves in two steps, each checked:
   - **The package:** Michigan's snapshot is built in the new format alongside its current files, and the package reads
     it. Every Michigan number must come out identical (the parity tests, the site tests, the six data files).
   - **The site:** waterledger.org/mi switches to the new files when the state pages are rebuilt on the shared format,
     with the page-vs-Python parity check passing. The old files are retired only after that.
   - **The build (Oct 30, 2026):** `waterledger build-state MI` downloads Michigan's sources (`states/mi/fetch.py`) and
     builds on GitHub like any other state, so its snapshot no longer depends on a site deploy. `waterledger build mi`
     stays for building from a cache, one part at a time.

## Build order

1. A "build one state" workflow, run on Ohio in Actions without uploading, to prove the jobs work there.
2. The snapshot format: the same files a state's waterledger.org pages would read, with JSON Schema.
3. Resumable stages and progress bars in the builders; the fallback prompt.
4. R2 upload and the manifest, once the bucket and the GitHub secret are set up (Cloudflare account steps are Andrew's).
5. The package reads snapshots first, then falls back.
