"""Design 0021's effect table: model 1.16's cell records against a run with the chiller change alone, p50s per 100 MW of IT.

Arguments: pairs of name=before.json,after.json (cell records as era5's runner writes them; the after runs made in memory with
docs/research/cooling-power-evidence/phoenix_run.py on the commit that made the change, with nothing written to the cache).
  .venv/bin/python -B docs/methods/chillers/effect.py "Grand Rapids=~/.cache/.../model1.16/43.00_-85.75.json,gr.json" ...
"""
import json
import os
import sys

FIELDS = (("pue_avg", "PUE a year", 3), ("pue_peak_1in10", "hottest-hour PUE", 3), ("power_mw_peak_1in10", "hottest hour, MW", 1),
          ("consumed_avg", "evaporated, MGD", 3))


def plant(rec, name):
    return rec["per_100mw"] if rec.get("plant", "shared") == name else rec["per_100mw_plants"][name]


def main(pairs):
    print("| Place | Plant | Design | " + " | ".join(f"{label}, 1.16 → 1.17" for _, label, _ in FIELDS) + " |")
    print("|---|---|---|" + "---|" * len(FIELDS))
    for pair in pairs:
        name, files = pair.split("=", 1)
        before, after = (json.load(open(os.path.expanduser(f))) for f in files.split(","))
        for pl in ("shared", "chilled", "warm"):
            for d in ("dry", "hybrid", "towers"):
                a, b = plant(before, pl)[d], plant(after, pl)[d]
                cells = " | ".join(f"{a[k]['p50']:.{n}f} → {b[k]['p50']:.{n}f}" for k, _, n in FIELDS)
                print(f"| {name} | {pl} | {d} | {cells} |")


if __name__ == "__main__":
    main(sys.argv[1:])
