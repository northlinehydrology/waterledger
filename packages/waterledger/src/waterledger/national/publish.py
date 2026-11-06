"""waterledger publish ST --dir SNAP: upload a snapshot written and checked on this machine to data.waterledger.org (the R2 bucket
waterledger-data), the way the build-state workflow uploads one it built.

The snapshot published is the one checked: check-snapshot must have recorded its checks in the manifest. A published snapshot never
changes, so a date data.waterledger.org already has stops it before anything is sent. The files go up first, the manifest after them
and the state's latest.json last, so a reader never finds a manifest whose files are not all there. R2 is reached as
waterledger_data.r2 sets up (WATERLEDGER_R2=wrangler, or the R2_* credentials), with the bucket named here.
"""
import json, os, tempfile, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor

BUCKET = "waterledger-data"
BASE = "https://data.waterledger.org"
TYPES = {".json": "application/json", ".parquet": "application/vnd.apache.parquet", ".csv": "text/csv"}


def _get(url):
    """(status, body): 404 is an answer; anything else that fails is raised, since publishing on a guess could overwrite."""
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "waterledger-publish"}), timeout=30) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return 404, None
        raise


def publish(state, root, date=None, build=None, store=None, get=_get, base=BASE, workers=8, say=print):
    """Upload root/<ST>/<date>/ (the newest date when none is given), with `build` (the build report) as build.json; returns the
    manifest's URL."""
    from waterledger.national.snapshot import pointer
    st = state.upper()
    if date is None:
        dates = sorted(os.listdir(os.path.join(root, st)))
        if not dates:
            raise SystemExit(f"no snapshot under {os.path.join(root, st)}")
        date = dates[-1]
    folder = os.path.join(root, st, date)
    manifest = json.load(open(os.path.join(folder, "manifest.json")))
    if not manifest.get("checks"):
        raise SystemExit(f"{st}/{date} has no checks in its manifest: run `waterledger check-snapshot {st} --dir {root}` first")
    if store is None:
        from waterledger_data import r2
        store = r2.from_env(bucket=BUCKET)
        if store is None:
            raise SystemExit("R2 is off: set WATERLEDGER_R2=wrangler (the wrangler login on this machine) or R2_ACCOUNT_ID, R2_ACCESS_KEY_ID "
                             "and R2_SECRET_ACCESS_KEY")
    code, _ = get(f"{base}/{st}/{date}/manifest.json")
    if code != 404:
        raise SystemExit(f"{st}/{date} is already published and a published snapshot never changes: write it again with --date {date}.2 "
                         "(or the next free number), check it and publish that")
    code, body = get(f"{base}/{st}/latest.json")               # read before anything is written
    old = json.loads(body) if code == 200 else None

    files = sorted(os.path.relpath(os.path.join(d, f), folder) for d, _, names in os.walk(folder) for f in names)
    files = [f for f in files if f != "manifest.json"]
    up = lambda f: store.publish(f"{st}/{date}/{f}", os.path.join(folder, f), TYPES.get(os.path.splitext(f)[1], "application/octet-stream"))
    with ThreadPoolExecutor(workers) as pool:
        for i, _ in enumerate(pool.map(up, files), 1):        # map raises the first failure, before the manifest goes up
            if i % 50 == 0:
                say(f"{i} of {len(files)} files up")
    if build:
        store.publish(f"{st}/{date}/build.json", build, TYPES[".json"])
    store.publish(f"{st}/{date}/manifest.json", os.path.join(folder, "manifest.json"), TYPES[".json"])
    latest = pointer(old, st, date, manifest["model_version"])
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "latest.json")
        json.dump(latest, open(p, "w"))
        store.publish(f"{st}/latest.json", p, TYPES[".json"], cache_control="max-age=300")
    say(f"{len(files)} files" + (", build.json" if build else "") + f", the manifest and latest.json are up: {json.dumps(latest)}")
    return f"{base}/{st}/{date}/manifest.json"
