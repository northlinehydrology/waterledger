# Release 3.10.0 (model 1.8): the steps after the runs

The code is on branch `release-1.8` (the whole stack: the ERA5 path, quantile mapping, the station links, the ERA5 check and
add-a-state, the hour blocks, snapshot format 3, Michigan on cells, `MODEL_VERSION` 1.8). What is left needs the four states'
runs. Run the steps in order from a checkout of `release-1.8` (`uv sync` first).

**Approvals.** Every step that publishes, tags or deploys needs Andrew's word first, each time.

**Where the snapshots are built.** On the Mac, not on GitHub. The runs are there (`~/.cache/waterledger/era5/runs/model1.8`)
and in the private bucket `waterledger-raw`, which the `build-state` workflow can't reach.

## 1. The runs are complete

```bash
for st in MI OH VA TX; do uv run waterledger era5 cells $st --json --no-r2; done
```

- **Done when:** each line says `"complete": true`: Michigan 272 cells, Ohio 203, Virginia 148 and Texas 616. Cells shared
  across state lines are counted in each state.
- **Optional, for the record:** `uv run waterledger era5 check ST` (exit 0 is a pass; `docs/add-a-state.md`, step 3).

## 2. Build and check the four format 3 snapshots

The national tier first. The layers are cached from the model 1.7 builds, so `build-state` resumes them; its cooling stage
now only records the division stations.

```bash
for st in OH VA TX; do uv run waterledger build-state $st --out build-report --no-checks && uv run waterledger snapshot $st --out snapshots; done
```

Michigan's site files are rebuilt from its cells, then written into its snapshot. The site folder is a scratch one, so the
Northline site isn't touched yet.

```bash
export WATERLEDGER_SITE=$PWD/release-site
uv run waterledger build-state MI
uv run waterledger snapshot MI --out snapshots
```

Then the checks, for every state:

```bash
for st in MI OH VA TX; do uv run waterledger check-snapshot $st --dir snapshots || echo "$st FAILED"; done
```

- **Done when:** every `check-snapshot` exits 0.
- **What the checks cover:** coverage, 50 sampled places through every design, every place on a cell with results, every
  cell's flows closing, and every corrected cell's stations in the manifest.
- **Then by hand** (`docs/add-a-state.md`, step 5):
  - three places per state against what you know of them;
  - Gaines, Lorain and Virginia Beach against the station check (`docs/methods/era5-station-check.md`).

## 3. The site's data and the parity check (Northline)

This needs Northline's change for cells, which is planned in `northline-cells-plan.md` in the session notes and not
built here. Run it in the northline repo, reading the local snapshots, not the published ones:

```bash
.venv/bin/python -m engine.products.mi_data /path/to/waterledger/snapshots/MI/<date>
.venv/bin/python -c "from engine.products import state_data as s; [s.build(st, f'/path/to/waterledger/snapshots/{st}/<date>', s.SITE + f'/{st.lower()}/data') for st in ('OH', 'VA', 'TX')]"
.venv/bin/python -m engine.check_parity
```

- **Done when:** `check_parity` passes for all four states. Its cases cool on cells: the page's numbers equal the package's.

## 4. Andrew's local check of waterledger.org

Serve the site locally, the way Northline's deploy notes describe, and check four places:
- one in each state;
- a moved place (Akron township, MI);
- a corrected shore place (Lorain, OH);
- the regions' starting views.

**Done when:** Andrew says so.

## 5. Publish the snapshots (Andrew's approval)

The workflow's upload step would rebuild on GitHub without the runs. So the four local snapshots are uploaded as they are,
with the same steps the workflow takes:
- refuse a date already published;
- upload the folder: its files, `inputs/` and `cells/` (cells are read on demand, so they must be there);
- upload `build.json`;
- write `latest.json` with `latest-json --dir`, so they're filed under model 1.8 and 3.9 packages keep reading 1.7.

With an R2 token for `waterledger-data` in the environment (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`,
`R2=https://<account>.r2.cloudflarestorage.com`):

```bash
for st in MI OH VA TX; do
  DATE=$(ls snapshots/$st)
  aws s3api head-object --bucket waterledger-data --key $st/$DATE/manifest.json --endpoint-url $R2 && { echo "$st/$DATE is published already"; continue; }
  aws s3 cp s3://waterledger-data/$st/latest.json old-latest-$st.json --endpoint-url $R2 || true
  aws s3 cp --recursive snapshots/$st/$DATE s3://waterledger-data/$st/$DATE --endpoint-url $R2
  [ -f build-report/${st}_build.json ] && aws s3 cp build-report/${st}_build.json s3://waterledger-data/$st/$DATE/build.json --endpoint-url $R2
  uv run waterledger latest-json $st $DATE --from old-latest-$st.json --dir snapshots > latest-$st.json
  aws s3 cp latest-$st.json s3://waterledger-data/$st/latest.json --endpoint-url $R2 --cache-control "max-age=300"
done
```

- **Done when:** each `https://data.waterledger.org/ST/latest.json` has `by_model["1.8"]` equal to its date, and
  `by_model["1.7"]` still on the old one.
- **Without a token:** the same steps work with `npx wrangler r2 object put waterledger-data/<key> --file <f> --remote`,
  one file at a time. That is slower: Texas's 616 cells at 2-3 s each is about half an hour.

## 6. Tag the release (Andrew's approval)

1. Merge `release-1.8` into `main` (by pull request, or as Andrew prefers). The `tests` workflow must pass.
2. Tag:

```bash
git tag v3.10.0 && git push origin v3.10.0
```

- **Done when:** the `publish` workflow has put `waterledger`, `waterledger-data` and `waterledger-models` 3.10.0 on PyPI,
  and `pip install waterledger==3.10.0` in a clean environment gives `MODEL_VERSION` 1.8.
- **Before tagging:** the changelog's heading becomes `## 3.10.0 (<date>)`. The state briefs (`docs/methods/build_briefs.py`)
  are rewritten from the published snapshots.

## 7. Deploy waterledger.org (Andrew's approval)

Northline's deploy, from its `deploy/` notes, with the site data from step 3.

**Done when:** waterledger.org/mi, /oh, /va and /tx show model 1.8 and a place's cooling from its cell.

## Not in this release

- **Average power on the 1-in-10-year peak day** (Andrew, Nov 4), with the power-plant water on that day that follows from
  it, shown in the detailed calculator. It needs a new output from every run, so it waits for the next model's runs.
- **The CDS source for ERA5** (needs an ECMWF key).
- **States outside the lower 48.**
