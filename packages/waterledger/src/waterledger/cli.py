"""waterledger build-state <ST>: build a state's data. waterledger build <state> [all|estimates|waters|power]: Michigan's site
data, part by part (paths from waterledger_data.config); kept for scripts, build-state MI runs the same build."""
import argparse, sys

from waterledger.states import STATES, builder


def _build_site(state, part="all"):
    m = builder(state)
    parts = {"estimates": m.main, "waters": m.build_waters, "power": m.build_power}
    for p in (["estimates", "waters", "power"] if part == "all" else [part]):
        parts[p]()


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
    sn = sub.add_parser("snapshot", help="write a state's snapshot files from its built data (run build-state first)")
    sn.add_argument("state")
    sn.add_argument("--out", required=True)
    sn.add_argument("--date", default=None)
    a = ap.parse_args(argv)
    if a.cmd == "latest-json":
        import json, os
        from waterledger.national.snapshot import pointer
        from waterledger_models import MODEL_VERSION
        print(json.dumps(pointer(json.load(open(a.old)) if a.old and os.path.exists(a.old) else None, a.state.upper(), a.snapshot_id, MODEL_VERSION)))
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
