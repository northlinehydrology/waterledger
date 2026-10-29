"""One folder per state (states/<st>/): a builder that writes the state's site data, and a provider that answers for its
places (Place, Context, Estimate). A state without a folder, or a part its folder doesn't provide, is answered by the
national tier (waterledger.national). Michigan is the full version."""
import importlib

STATES = {"mi": "Michigan"}
FIPS = {"01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT", "10": "DE", "11": "DC", "12": "FL",
        "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN", "19": "IA", "20": "KS", "21": "KY", "22": "LA", "23": "ME",
        "24": "MD", "25": "MA", "26": "MI", "27": "MN", "28": "MS", "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH",
        "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI",
        "45": "SC", "46": "SD", "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA", "54": "WV", "55": "WI",
        "56": "WY"}


def state_for_fips(fips):
    if fips not in FIPS:
        raise KeyError(f"no state with FIPS code {fips!r}")
    return FIPS[fips]


def builder(state):
    """The module that writes a state's site data (waterledger build <state>)."""
    state = state.lower()
    if state not in STATES:
        raise KeyError(f"No builder for {state!r}; have {sorted(STATES)}")
    return importlib.import_module(f"waterledger.states.{state}.build")


class Provider:
    """Answers for one state: each call goes to the state's own provider if it has that function, else to the national one."""

    def __init__(self, state):
        self.state = state.upper()
        self.own = importlib.import_module(f"waterledger.states.{state.lower()}.provider") if state.lower() in STATES else None
        self.national = importlib.import_module("waterledger.national.provider")

    def __getattr__(self, name):
        if self.own is not None and hasattr(self.own, name):
            return getattr(self.own, name)
        fn = getattr(self.national, name)
        return lambda *a, **k: fn(self.state, *a, **k)

    def __repr__(self):
        return f"Provider({self.state}: {'own and national' if self.own else 'national'})"


def provider(state):
    """The provider for a state (postal code): its own where it has one, national for the rest."""
    if state.upper() not in FIPS.values():
        raise KeyError(f"no state {state!r}")
    return Provider(state)


def __getattr__(name):
    if name in STATES:
        return importlib.import_module(f"waterledger.states.{name}")
    raise AttributeError(name)
