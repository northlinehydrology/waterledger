"""The states: postal codes and names, and the provider that answers for a state's places (Place, Context, Estimate), the national tier
for every state (waterledger.national) with the state's own layers on it (design 0011). states/mi/ keeps Michigan's former builder and
provider, deprecated, through 3.x (`waterledger build mi` still writes its site files)."""
import importlib

STATES = {"mi": "Michigan"}
FIPS = {"01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT", "10": "DE", "11": "DC", "12": "FL",
        "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN", "19": "IA", "20": "KS", "21": "KY", "22": "LA", "23": "ME",
        "24": "MD", "25": "MA", "26": "MI", "27": "MN", "28": "MS", "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH",
        "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI",
        "45": "SC", "46": "SD", "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA", "54": "WV", "55": "WI",
        "56": "WY"}
NAMES = {"AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
         "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
         "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
         "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico",
         "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island",
         "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
         "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming"}


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
    """Answers for one state, through the national provider: every state, Michigan included, is the national base plus its own layers
    (design 0011). `own` stays for code that checked it, and is None; Michigan's former provider (waterledger.states.mi.provider) is kept,
    deprecated, through 3.x."""

    def __init__(self, state):
        self.state = state.upper()
        self.own = None
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
