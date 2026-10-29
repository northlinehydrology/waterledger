"""waterledger build <state> [all|estimates|waters|power|moratoria]: write a state's site data (paths from waterledger_data.config)."""
import argparse

from waterledger.states import STATES, builder


def main(argv=None):
    ap = argparse.ArgumentParser(prog="waterledger", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="write a state's site data")
    b.add_argument("state", choices=sorted(STATES))
    b.add_argument("part", nargs="?", default="all", choices=["all", "estimates", "waters", "power", "moratoria"])
    bs = sub.add_parser("build-state", help="build a state's national-tier data from the public sources (resumes where it left off)")
    bs.add_argument("state")
    bs.add_argument("--out", default=None, help="write a build report here")
    a = ap.parse_args(argv)
    if a.cmd == "build-state":
        from waterledger.national.build import build
        build(a.state, a.out)
        return
    m = builder(a.state)
    parts = {"estimates": m.main, "waters": m.build_waters, "power": m.build_power, "moratoria": m.build_moratoria}
    for p in (["estimates", "waters", "power", "moratoria"] if a.part == "all" else [a.part]):
        parts[p]()


if __name__ == "__main__":
    main()
