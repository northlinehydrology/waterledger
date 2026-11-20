"""Each state's reviewed rules for large new water users, as data: one file per state in rules/<st>.toml, every line read against its primary source on
the file's `checked` date. A state with no file has no lines and says so (levels.NOT_REVIEWED_NOTE). Nothing here changes an estimate: the lines feed the
levels a reader sees (waterledger.levels) and the words a display shows beside them.

A file holds:
  checked              the date every line was last read against its source (YYYY-MM-DD)
  [withdrawals]        (a state with no numeric line has only `summary` and `sources`: the reader sees the summary and no level) lines for water pumped or taken at a site, in million gallons a day. Each [[withdrawals.lines]] has a `key`, `mgd`, the `level` above
                       it, a `tag` (a card's few words), and optionally: `flag` (the sentence a reader sees when an estimate exceeds a permit line), `measure`
                       ("withdrawn", the default, or "consumed": water used up), `period` ("capacity": the peak day; "30 days" or "90 days": the highest month
                       for water withdrawn, the highest 90 days for water used up; the section's `period` where absent; levels.tested_on), `at_least` (the
                       rule reads "at least" rather than "more than"), `where` ("great_lakes_basin" or "outside_great_lakes_basin") and `source` (a list of
                       "ground", "surface" and "lake": a Great Lake itself), `huc` (HUC prefixes: the line applies only in those river basins, e.g. a basin
                       commission's), `counties` (five-digit county FIPS codes: only in those whole counties) and `areas` (groups in rules/<st>_areas.json:
                       only in places inside those areas; a place partly inside sees both rules, levels.withdrawal's `inside`). `summary` words the lines for a card, `utility` says what a
                       utility serving the campus needs, `screening` names a state screening tool where one exists; `below_tag` the card's words under every line, where the
                       site's default (below the state's reporting level) doesn't fit; `basin_summary` and `lake_summary`
                       word the lines in the Great Lakes basin and for an intake in a Great Lake, where they differ.
  [discharge]          `permit_note`: what a discharge permit usually carries beyond the federal minimum (a phosphorus limit, a temperature rule)
  [septic]             [[septic.lines]]: `below_gpd` (under) or `max_gpd` (up to) and `text`, the last line with neither; who approves an on-site system by its flow
  [lake_erie]          `note`: the state's phosphorus target for Lake Erie, for a place that drains to it
  [large_load]         `mw`, `text` and `caption`: the large-load line in force, if any, and `utility`, a pattern for the utilities (EIA names) whose tariff sets it
  [[sources]]          `id`, `short` (a link's words), `title`, `publisher`, `url`, `read` (the date the source was read; the file's `checked` where absent)
"""
import functools
import json
import tomllib
from importlib import resources

COMPACT_USE_MGD = 5.0           # Great Lakes Compact, Section 4.6: prior notice to every party of a proposal for a new or increased consumptive use of 5 million gallons a day or more, averaged over any 90 days


@functools.cache
def load(state):
    """A state's rules file as a dict, or None where the state's rules aren't reviewed yet."""
    f = resources.files("waterledger").joinpath("rules", f"{state.lower()}.toml")
    if not f.is_file():
        return None
    with f.open("rb") as fh:
        out = tomllib.load(fh)
    out["state"] = state.upper()
    return out


@functools.cache
def areas(state):
    """rules/<st>_areas.json: which places are in the areas a state's lines name where those areas don't follow county lines (tools/rule_areas.py),
    or None. {"groups": {group: [area names]}, "places": {geoid: {group: {"share", "names"}}}, "in", "part", "sources", "read"}."""
    f = resources.files("waterledger").joinpath("rules", f"{state.lower()}_areas.json")
    if not f.is_file():
        return None
    with f.open("rb") as fh:
        return json.load(fh)


def place_areas(state, geoid):
    """A place's membership in its state's rule areas: {group: {"status": "in" or "part", "share", "names"}}; empty where it is in none."""
    A = areas(state)
    if not A or not geoid:
        return {}
    return {g: {"status": "in" if v["share"] >= A["in"] else "part", **v} for g, v in A["places"].get(str(geoid), {}).items()}


def states():
    """The states with a reviewed rules file, upper case."""
    d = resources.files("waterledger").joinpath("rules")
    return sorted(p.name.removesuffix(".toml").upper() for p in d.iterdir() if p.name.endswith(".toml"))


def withdrawals(state):
    """context.withdrawals for a state: the Compact's line (used only for a place on the Great Lakes or in their basin) and, where the state's rules are
    reviewed, its lines and the period they are tested on."""
    R = load(state)
    out = {"compact_use_mgd": COMPACT_USE_MGD}
    if R and R.get("withdrawals", {}).get("lines"):
        W = R["withdrawals"]
        out.update(lines=[dict(x) for x in W["lines"]], period=W.get("period", "30 days"))
    elif R and R.get("withdrawals", {}).get("summary"):
        out["no_line"] = R["withdrawals"]["summary"]       # reviewed, and the state sets no numeric line a site's pumping can be tested on (Texas: districts set their own)
    return out


def jurisdiction(state):
    """Jurisdiction.rules: each withdrawal line and each other rule a file carries, with its sources, for a report to list."""
    R = load(state)
    if not R:
        return []
    out = [{"topic": "withdrawal", "key": x["key"], "mgd": x["mgd"], "tag": x["tag"], **({"where": x["where"]} if "where" in x else {}),
            **({"source": x["source"]} if "source" in x else {}), **{k: x[k] for k in ("huc", "counties") if k in x}, "sources": x.get("sources", [])} for x in R.get("withdrawals", {}).get("lines", [])]
    for k in ("discharge", "lake_erie", "large_load"):
        if k in R:
            out.append({"topic": k, **{a: b for a, b in R[k].items()}})
    for x in R.get("septic", {}).get("lines", []):
        out.append({"topic": "septic", **x})
    return out


def sources(state):
    """{id: source} for a state's rules, each with the date it was read."""
    R = load(state) or {}
    return {s["id"]: {**s, "read": str(s.get("read", R.get("checked")))} for s in R.get("sources", [])}
