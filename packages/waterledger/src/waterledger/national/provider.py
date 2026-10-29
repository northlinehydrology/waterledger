"""The national provider: answers for any state from federal data (design 0002). Each function takes the state it
answers for; the parts not built yet say which step of design 0002 brings them."""
import functools

from waterledger import states

STEPS = {"context": "steps 3 to 5 (supply, wastewater, receiving waters, climate, energy)",
         "estimate": "steps 4 and 6 (climate and the generic estimate)"}


class NotYet(NotImplementedError):
    """A national-tier part that is still being built."""


def _not_yet(part, state):
    raise NotYet(f"{state}: the national tier's {part} is not built yet; it comes in design 0002 {STEPS[part]}. Michigan is available now.")


@functools.lru_cache(maxsize=8)
def _places(state):
    from waterledger_data import census
    return census.places(next(f for f, s in states.FIPS.items() if s == state))


def _display(r):
    """How a place is written: cities, towns and villages by name, townships and counties with their kind."""
    return r["base"] if r["level"] == "place" else f"{r['base']} {r['kind'].title()}" if r["level"] == "township" else r["name"]


def find(state, name, county=None):
    """GEOID of a place by name ("Columbus city", "Columbus", "Loudoun County"), optionally within a county."""
    g = _places(state)
    n = name.lower().strip()
    if county:
        g = g[g.county.str.lower() == county.lower().replace(" county", "").strip()]
    exact = g[(g.name.str.lower() == n) | (g.base.str.lower() == n)]
    hits = exact if len(exact) else g[g.name.str.lower().str.startswith(n)]
    if len(hits) == 1:
        return hits.iloc[0].geoid
    opts = [f"{r.name} ({r.county} County)" for r in hits.head(6).itertuples()]
    raise KeyError(f"{name!r} in {state} matches {opts or 'nothing'}; give the full name (e.g. 'Columbus city'), a county, or the GEOID")


def place(state, geoid):
    from waterledger.place import Place
    g = _places(state)
    hit = g[g.geoid == str(geoid)]
    if not len(hit):
        raise KeyError(f"no {state} place with GEOID {geoid}")
    r = hit.iloc[0]
    return Place(geoid=r.geoid, name=_display(r), kind=r.kind.lower(), state=state, county=r.county, county_fips=r.county_fips,
                 lat=round(float(r.lat), 4), lon=round(float(r.lon), 4))


def context(state, place):
    _not_yet("context", state)


def estimate(state, site):
    _not_yet("estimate", state)
