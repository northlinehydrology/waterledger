"""Tag the national-tier tests with the states they need (a marker state_<st> for each state in states.toml), so a state's build
job runs only its own: pytest -m "live and state_oh". A test's state is read from its parameters: a postal code, or a place query
ending in one ("Columbus city, OH")."""
import os, re, tomllib

import pytest

STATES = tuple(tomllib.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "states.toml"), "rb")))
# tests whose state can't be read from their parameters. test_hotter_climate_uses_more_water_with_towers has no state: it needs two whole states' climate, so
# it runs nightly, not in a state's build job, where it took over half an hour to rebuild the other state.
BY_NAME = {"test_counts_and_independent_cities_once": ("VA", "OH"), "test_statewide_impairment_table": ("OH",),
           "test_lake_source_is_great_lakes_only": ("TX",),
           "test_ohio_snapshot": ("OH",), "test_snapshot_equals_live": ("OH",), "test_michigan_point_lookup_uses_michigan_places": ("MI",),
           "test_ohio_franklin_2024": ("OH",), "test_texas_travis_2024": ("TX",), "test_virginia_loudoun_2024": ("VA",)}
ENDS = re.compile(r", (" + "|".join(STATES) + r")$")


def pytest_configure(config):
    for st in STATES:
        config.addinivalue_line("markers", f"state_{st.lower()}: needs {st}'s national-tier data")


def _states(item):
    name = item.originalname or item.name
    found = set(BY_NAME.get(name, ()))
    for v in getattr(getattr(item, "callspec", None), "params", {}).values():
        if isinstance(v, str):
            if v in STATES:
                found.add(v)
            m = ENDS.search(v)
            if m:
                found.add(m.group(1))
    return found


def pytest_collection_modifyitems(config, items):
    for item in items:
        for st in _states(item):
            item.add_marker(getattr(pytest.mark, f"state_{st.lower()}"))
