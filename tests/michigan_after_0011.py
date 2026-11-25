"""Design 0011 step 6: every Michigan answer again, now from Michigan's snapshot on the base with its own layers, against the before record
(tests/data/michigan_before_0011.json.xz), and the list of differences for Andrew: each field that changed, at how many places, the size of the
change and examples, so each can be given a cause (expected: the base or a layer is better; bug: a better Michigan source dropped or misread).

    uv run python tests/michigan_after_0011.py <snapshot folder> [--out differences.md] [--json differences.json]
"""
import argparse
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def use_snapshot(folder):
    """Answer Michigan from the snapshot in `folder` (a local build), not the published one."""
    from waterledger.national import data, provider
    snap = data.SnapshotData("MI", folder)
    real = data.state_data

    def sd(state, *a, **k):
        return snap if state.upper() == "MI" else real(state, *a, **k)
    data.state_data = provider.state_data = sd
    provider._served.cache_clear() if hasattr(provider._served, "cache_clear") else None
    return snap


def walk(a, b, path, out):
    """Every leaf path where a and b differ: [(path, before, after)]."""
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            walk(a.get(k, "<absent>"), b.get(k, "<absent>"), f"{path}/{k}", out)
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            walk(x, y, f"{path}[{i}]", out)
    elif a != b:
        out.append((path, a, b))


def field(path):
    """A path with its list positions folded, so a field's differences group across places: /ok/water/withdrawn/avg/mid."""
    return re.sub(r"\[\d+\]", "[]", path)


def compare(before, after):
    rows = collections.defaultdict(list)
    for key in sorted(before):
        geoid, case = key.split("|", 1)
        d = []
        walk(before[key], after.get(key, "<absent>"), "", d)
        for p, x, y in d:
            rows[(case if case in ("place", "context", "reference") else "estimate", field(p))].append((geoid, case, x, y))
    return rows


def rel(x, y):
    try:
        return abs(float(y) - float(x)) / abs(float(x)) if float(x) else None
    except (TypeError, ValueError):
        return None


def report(rows, before):
    places = {k.split("|")[0] for k in before}
    out = [f"# Michigan on the base: differences from the before record", "",
           f"{len(before):,} cases at {len(places):,} places; {sum(len(v) for v in rows.values()):,} differing values in {len(rows)} fields.", "",
           "| Part | Field | Places | Values | Largest relative change | Example (place, before → after) |", "|---|---|---|---|---|---|"]
    for (part, f), v in sorted(rows.items(), key=lambda kv: (-len({g for g, *_ in kv[1]}), kv[0])):
        n = len({g for g, *_ in v})
        rs = [r for r in (rel(x, y) for _, _, x, y in v) if r is not None]
        g, case, x, y = v[0]
        ex = f"{g} {case}: {json.dumps(x)[:60]} → {json.dumps(y)[:60]}"
        out.append(f"| {part} | `{f}` | {n:,} | {len(v):,} | {max(rs):.3g} |" if rs else f"| {part} | `{f}` | {n:,} | {len(v):,} | |")
        out[-1] += f" {ex} |"
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("snapshot")
    ap.add_argument("--out")
    ap.add_argument("--json")
    ap.add_argument("--places", type=int, help="a sample of this many places, for a quick look")
    a = ap.parse_args(argv)
    use_snapshot(a.snapshot)
    import random
    import michigan_reference as mr
    before = mr.load()
    geoids = sorted({k.split("|")[0] for k in before})
    if a.places:
        geoids = sorted(random.Random(1).sample(geoids, a.places))
        before = {k: v for k, v in before.items() if k.split("|")[0] in set(geoids)}
    after = mr.results(geoids)
    rows = compare(before, after)
    md = report(rows, before)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(md)
    if a.json:
        json.dump({f"{p}|{f}": v for (p, f), v in rows.items()}, open(a.json, "w", encoding="utf-8"), default=str)
    print(md if not a.out else f"wrote {a.out}: {len(rows)} fields differ")


if __name__ == "__main__":
    main()
