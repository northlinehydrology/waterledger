"""The national provider. Each function takes the state it answers for; the parts not built yet say which step of design
0002 brings them."""

STEPS = {"places": "step 2 (places for any state)", "context": "steps 3 to 5 (supply, wastewater, receiving waters, climate, energy)",
         "estimate": "steps 4 and 6 (climate and the generic estimate)"}


class NotYet(NotImplementedError):
    """A national-tier part that is still being built."""


def _not_yet(part, state):
    raise NotYet(f"{state}: the national tier's {part} is not built yet; it comes in design 0002 {STEPS[part]}. Michigan is available now.")


def find(state, name, county=None):
    _not_yet("places", state)


def place(state, geoid):
    _not_yet("places", state)


def context(state, place):
    _not_yet("context", state)


def estimate(state, site):
    _not_yet("estimate", state)
