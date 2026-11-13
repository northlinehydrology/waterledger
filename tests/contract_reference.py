"""Write tests/data/estimates_before_contract.json.gz: whole estimates as they were before design 0010's facility contract (step 1), so each step of the
move can be held to them to the last bit (test_contract_identity.py). Two places in each published state (the brief's example, and a Great Lakes
shore place or a second city), every cooling design, every wastewater choice, the three cooling plants, by_design, to_bmi_config, and the model run
at the place (weather="local") for each state's example. A choice the package refuses is recorded with its message, so the refusals stay the same too.
Written once, on the national snapshots and Michigan site data cached on Nov 12, 2026; not rerun.

    uv run python tests/contract_reference.py
"""
import gzip
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

PLACES = {"MI": ("Gaines charter township, MI", "Muskegon city, MI"), "OH": ("Columbus city, OH", "Cleveland city, OH"),
          "VA": ("Loudoun County, VA", "Richmond city, VA"), "TX": ("Austin city, TX", "Granbury city, TX"),
          "WI": ("Madison city, WI", "Milwaukee city, WI"), "IN": ("Lebanon city, IN", "Gary city, IN"),
          "PA": ("Pittsburgh city, PA", "Erie city, PA"), "MN": ("Farmington city, MN", "Duluth city, MN"),
          "GA": ("Fayetteville city, GA", "Atlanta city, GA"), "IL": ("Aurora city, IL", "Chicago city, IL")}
DESIGNS = ("dry", "assist", "hybrid", "towers", "lake")
WASTEWATER = (None, "sewer", "septic", "water", "reuse")
PLANTS = ("shared", "warm", "chilled")
MW = 300


def _run(fn):
    try:
        return {"ok": fn()}
    except Exception as e:                       # noqa: BLE001  a refusal is part of the behavior held
        return {"error": f"{type(e).__name__}: {e}"}


def cases():
    """{key: thunk} for every case, the key naming it."""
    import waterledger as wl
    out = {}
    for st, queries in PLACES.items():
        for i, q in enumerate(queries):
            p = wl.place(q)
            site = lambda cooling="dry", plant="shared", **kw: wl.Site(place=p, facility=wl.DataCenter(it_mw=MW, cooling=cooling, plant=plant), **kw)
            for d in DESIGNS:
                for w in WASTEWATER:
                    src = "lake" if d == "lake" else None
                    out[f"{q}|{d}|{w}|shared|region"] = (lambda s: lambda: s.estimate().model_dump(mode="json"))(site(d, source=src, wastewater=w))
            for pl in PLANTS[1:]:
                out[f"{q}|towers|None|{pl}|region"] = (lambda s: lambda: s.estimate().model_dump(mode="json"))(site("towers", pl))
            out[f"{q}|by_design"] = (lambda s: lambda: s.by_design(("dry", "assist", "hybrid", "towers")).model_dump(mode="json"))(site())
            for d in ("hybrid", "lake"):
                out[f"{q}|{d}|bmi"] = (lambda s: lambda: list(s.to_bmi_config(design_db=31.5)))(site(d, source="lake" if d == "lake" else None))
            if i == 0:
                for d in ("dry", "hybrid"):
                    out[f"{q}|{d}|None|shared|local"] = (lambda s: lambda: s.estimate(weather="local").model_dump(mode="json"))(site(d))
    return out


def results(keys=None):
    C = cases()
    return {k: _run(C[k]) for k in (keys or C)}


if __name__ == "__main__":
    R = results()
    path = os.path.join(HERE, "data", "estimates_before_contract.json.gz")
    with gzip.open(path, "wt", compresslevel=9) as f:          # about 7 MB as text
        json.dump(R, f, indent=0, sort_keys=True)
    bad = [k for k, v in R.items() if "error" in v]
    print(f"wrote {path}: {len(R)} cases, {len(bad)} refused", file=sys.stderr)
