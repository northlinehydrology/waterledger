"""One builder per state, each writing <site>/<state>/data/*.json. Michigan is the full version; others follow."""
import importlib

STATES = {"mi": "Michigan"}


def builder(state):
    if state not in STATES:
        raise KeyError(f"No builder for {state!r}; have {sorted(STATES)}")
    return importlib.import_module(f"waterledger.states.{state}")


def __getattr__(name):
    if name in STATES:
        return builder(name)
    raise AttributeError(name)
