"""waterledger build-state <ST>: build a state's data. waterledger era5 run <ST> --part k/n: model 1.8's cooling runs on ERA5 cells. waterledger
publish <ST> --dir <snapshot root>: upload a checked snapshot to data.waterledger.org. waterledger build <state> [all|estimates|waters|power]: Michigan's site
data, part by part (paths from waterledger_data.config); kept for scripts, build-state MI runs the same build."""
import argparse, os, sys

from waterledger.states import STATES, builder


def _build_site(state, part="all"):
    m = builder(state)
    parts = {"estimates": m.main, "waters": m.build_waters, "power": m.build_power}
    for p in (["estimates", "waters", "power"] if part == "all" else [part]):
        parts[p]()


def _era5(a):
    from waterledger.national import era5 as E
    from waterledger_data import era5, r2
    a.workers = a.workers or E.default_workers()
    if a.action == "check":
        from waterledger.national.era5_check import run_check
        rep = run_check(a.state, a.out, n=a.places, workers=a.workers, draws=a.draws, weather_only=a.weather_only,
                        places=E.state_places(a.state, a.snapshot))
        sys.exit(0 if rep["verdict"] == "pass" else 1)
    k, n = E.parse_part(a.part)
    cells = E.state_cells(a.state, a.snapshot)
    if a.action == "cells":
        parts = []
        for i in range(1, n + 1):
            ids = E.part(cells, i, n)
            parts.append({"part": f"{i}/{n}", "cells": len(ids), "done": sum(os.path.exists(E.result_path(c)) for c in ids),
                          "places": sum(len(cells[c]["places"]) for c in ids), "first": ids[0] if ids else None, "last": ids[-1] if ids else None})
        if a.json:
            import json
            total, done = sum(p["cells"] for p in parts), sum(p["done"] for p in parts)
            print(json.dumps({"state": a.state.upper(), "model_version": E.RUN_MODEL, "runs": E.RUNS, "cells": total, "done": done,
                              "complete": total > 0 and done == total, "parts": parts}))
            return
        for p in parts:
            print(f"{a.state.upper()} part {p['part']}: {p['cells']} cells ({p['first']} to {p['last']}), {p['done']} done, {p['places']} places")
        return
    store = None if a.no_r2 else r2.from_env()
    if a.action == "fetch":
        ids = [c for c in E.part(cells, k, n) if not era5.raw_path(c)]
        era5.fetch(ids)
        if store:
            for c in ids:
                E.push_raw(store, c)
        print(f"{len(ids)} cells fetched")
        return
    try:
        E.run_part(a.state, k, n, workers=a.workers, draws=a.draws, store=store, cells=cells)
    except KeyboardInterrupt:
        print(f"stopped; `waterledger era5 run {a.state.upper()} --part {a.part}` resumes where it stopped", file=sys.stderr)
        sys.exit(130)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="waterledger", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="write a state's site data")
    b.add_argument("state", choices=sorted(STATES))
    b.add_argument("part", nargs="?", default="all", choices=["all", "estimates", "waters", "power"])
    bs = sub.add_parser("build-state", help="build a state's data: Michigan from its own sources, others from the national sources (resumes where it left off)")
    bs.add_argument("state")
    bs.add_argument("--out", default=None, help="write a build report here")
    bs.add_argument("--no-checks", action="store_true", help="skip the statewide checks (run them on the snapshot instead)")
    ck = sub.add_parser("check-snapshot", help="run the statewide checks on a written snapshot and record them in its manifest")
    ck.add_argument("state")
    ck.add_argument("--dir", required=True, help="the snapshot root (the --out given to snapshot)")
    lj = sub.add_parser("latest-json", help="print a state's latest.json after publishing a snapshot: reads the old one from --from, if any")
    lj.add_argument("state")
    lj.add_argument("snapshot_id")
    lj.add_argument("--from", dest="old", default=None)
    lj.add_argument("--dir", default=None, help="the snapshot root: the snapshot's manifest gives the model it is filed under (else this package's model)")
    pb = sub.add_parser("publish", help="upload a snapshot written and checked here to data.waterledger.org (needs R2: WATERLEDGER_R2=wrangler or the R2_* credentials)")
    pb.add_argument("state")
    pb.add_argument("--dir", required=True, help="the snapshot root (the --out given to snapshot)")
    pb.add_argument("--date", default=None, help="the snapshot to publish (default the newest under --dir)")
    pb.add_argument("--build", default=None, help="the build report (build-state --out's ST_build.json), published as build.json")
    sn = sub.add_parser("snapshot", help="write a state's snapshot files from its built data (run build-state first)")
    sn.add_argument("state")
    sn.add_argument("--out", required=True)
    sn.add_argument("--date", default=None)
    e5 = sub.add_parser("era5", help="model 1.8's cooling runs on each place's ERA5 cell (design 0004): cells, fetch, run part by part, or check")
    e5.add_argument("action", choices=["cells", "fetch", "run", "check"],
                    help="cells: the parts and what is done; fetch: a part's weather only; run: fetch, correct and run; "
                         "check: the leave-one-station-out check of design 0005 (exit 0 pass, 1 fail)")
    e5.add_argument("state")
    e5.add_argument("--part", default="1/1", help="k/n: run the k-th of n parts (default 1/1, the whole state)")
    e5.add_argument("--workers", type=int, default=None, help="cells at once (default: the performance cores, 10 on an M3 Max)")
    e5.add_argument("--draws", type=int, default=None, help="Monte Carlo draws per cell (default the model's, 400)")
    e5.add_argument("--snapshot", default=None, help="the snapshot date whose places to use (default the latest)")
    e5.add_argument("--no-r2", action="store_true", help="leave R2 off even if it is set up")
    e5.add_argument("--json", action="store_true", help="cells: print the parts and what is done as JSON (complete: true when every cell has a result)")
    e5.add_argument("--places", type=int, default=12, help="check: places to run through the cooling model (default 12)")
    e5.add_argument("--weather-only", action="store_true", help="check: the weather part only (the check then can't pass)")
    e5.add_argument("--out", default=None, help="check: where to write check.json and check.md (default CACHE/era5/check/ST)")
    a = ap.parse_args(argv)
    if a.cmd == "era5":
        _era5(a)
        return
    if a.cmd in ("build-state", "build"):
        os.environ.setdefault("WATERLEDGER_WORKERS", str(os.cpu_count() or 1))    # a command, so safe for a process pool (cooling.run_locations)
    if a.cmd == "latest-json":
        import json
        from waterledger.national.snapshot import pointer
        from waterledger_models import MODEL_VERSION
        model = MODEL_VERSION
        if a.dir:                                       # a snapshot is filed under the model of its numbers: a format 3 one under 1.8, so 1.7 packages never read it
            model = json.load(open(os.path.join(a.dir, a.state.upper(), a.snapshot_id, "manifest.json")))["model_version"]
        print(json.dumps(pointer(json.load(open(a.old)) if a.old and os.path.exists(a.old) else None, a.state.upper(), a.snapshot_id, model)))
        return
    if a.cmd == "publish":
        from waterledger.national.publish import publish
        print("published", publish(a.state, a.dir, a.date, a.build))
        return
    if a.cmd == "snapshot":
        if a.state.upper() == "MI":                       # Michigan: from its own data, with its site files carried along
            from waterledger.states.mi.snapshot import write as write_mi
            print(write_mi(a.out, a.date))
        else:
            from waterledger.national.snapshot import write
            print(write(a.state, a.out, a.date))
        return
    if a.cmd == "build-state":
        if a.state.lower() in STATES:                     # a state with its own data (Michigan) builds from that, not the national tier
            from waterledger.states.mi.fetch import fetch_all
            fetch_all()
            _build_site(a.state.lower())
            return
        from waterledger.national.build import build
        build(a.state, a.out, run_checks=not a.no_checks)
        return
    if a.cmd == "check-snapshot":
        from waterledger.national.build import check_snapshot
        check_snapshot(a.state, a.dir)
        return
    if a.part == "all":
        print(f"note: `waterledger build-state {a.state.upper()}` runs the same build; `waterledger build` stays for building one part", file=sys.stderr)
    _build_site(a.state, a.part)


if __name__ == "__main__":
    main()
