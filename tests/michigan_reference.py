"""Write tests/data/michigan_before_0011.json.xz: every Michigan answer from the path design 0011 replaces (step 1), so the move onto the base can be
held to it place by place (step 6, tests/michigan_after_0011.py). For all 1,541 places: wl.place, place.context(), the provider's reference(), and
site.estimate() at 300 MW for every cooling design at the package's defaults, plus lake-source for the places on a Great Lake. A choice the package
refuses is recorded with its message. Identical answers are stored once (by hash), so the record stays small. Written once, from 3.27.0 and Michigan's
snapshot as cached; not rerun.

    uv run python tests/michigan_reference.py
"""
import hashlib
import json
import lzma
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
RECORD = os.path.join(HERE, "data", "michigan_before_0011.json.xz")
DESIGNS = ("dry", "assist", "hybrid", "towers")
MW = 300


def _run(fn):
    try:
        return {"ok": fn()}
    except Exception as e:                       # noqa: BLE001  a refusal is part of the behavior held
        return {"error": f"{type(e).__name__}: {e}"}


def cases(geoids=None):
    """{key: thunk}: "<geoid>|place", "|context", "|reference", "|<design>" and, on a Great Lake, "|lake"."""
    import waterledger as wl
    from waterledger import states
    P = states.provider("MI")
    shore = set(P.shore_geoids())
    out = {}
    for g in geoids or P.geoids():
        p = wl.place(geoid=g)
        out[f"{g}|place"] = (lambda p: lambda: p.model_dump(mode="json"))(p)
        out[f"{g}|context"] = (lambda p: lambda: p.context().model_dump(mode="json"))(p)
        out[f"{g}|reference"] = (lambda p: lambda: P.reference(p))(p)
        for d in DESIGNS:
            out[f"{g}|{d}"] = (lambda p, d: lambda: wl.Site(place=p, facility=wl.DataCenter(it_mw=MW, cooling=d)).estimate().model_dump(mode="json"))(p, d)
        if g in shore:
            out[f"{g}|lake"] = (lambda p: lambda: wl.Site(place=p, facility=wl.DataCenter(it_mw=MW, cooling="lake"), source="lake").estimate().model_dump(mode="json"))(p)
    return out


def results(geoids=None):
    C = cases(geoids)
    return {k: _run(C[k]) for k in C}


def pack(R):
    """{"keys": {key: hash}, "blobs": {hash: value}}: each distinct answer once."""
    keys, blobs = {}, {}
    for k, v in R.items():
        s = json.dumps(v, sort_keys=True, separators=(",", ":"))
        h = hashlib.sha256(s.encode()).hexdigest()[:20]
        keys[k] = h
        blobs.setdefault(h, v)
    return {"keys": keys, "blobs": blobs}


def load(path=RECORD):
    with lzma.open(path, "rt", encoding="utf-8") as f:
        d = json.load(f)
    return {k: d["blobs"][h] for k, h in d["keys"].items()}


if __name__ == "__main__":
    import waterledger
    t = time.time()
    R = results()
    meta = {"package": waterledger.__version__, "written": time.strftime("%Y-%m-%d"), "note": "design 0011 step 1"}
    with lzma.open(RECORD, "wt", encoding="utf-8", preset=9) as f:
        json.dump({"meta": meta, **pack(R)}, f, sort_keys=True, separators=(",", ":"))
    bad = [k for k, v in R.items() if "error" in v]
    print(f"wrote {RECORD}: {len(R)} cases, {len(bad)} refused, {os.path.getsize(RECORD) / 1e6:.1f} MB, {time.time() - t:.0f} s", file=sys.stderr)
