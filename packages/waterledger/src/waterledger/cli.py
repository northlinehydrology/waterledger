"""waterledger build <state> [all|estimates|waters|power]: write a state's site data (paths from waterledger_data.config)."""
import argparse

from waterledger.states import STATES, builder


def main(argv=None):
    ap = argparse.ArgumentParser(prog="waterledger", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="write a state's site data")
    b.add_argument("state", choices=sorted(STATES))
    b.add_argument("part", nargs="?", default="all", choices=["all", "estimates", "waters", "power"])
    bs = sub.add_parser("build-state", help="build a state's national-tier data from the public sources (resumes where it left off)")
    bs.add_argument("state")
    bs.add_argument("--out", default=None, help="write a build report here")
    sn = sub.add_parser("snapshot", help="write a state's snapshot files from its built data (run build-state first)")
    sn.add_argument("state")
    sn.add_argument("--out", required=True)
    sn.add_argument("--date", default=None)
    a = ap.parse_args(argv)
    if a.cmd == "snapshot":
        from waterledger.national.snapshot import write
        print(write(a.state, a.out, a.date))
        return
    if a.cmd == "build-state":
        from waterledger.national.build import build
        build(a.state, a.out)
        return
    m = builder(a.state)
    parts = {"estimates": m.main, "waters": m.build_waters, "power": m.build_power}
    for p in (["estimates", "waters", "power"] if a.part == "all" else [a.part]):
        parts[p]()


if __name__ == "__main__":
    main()
