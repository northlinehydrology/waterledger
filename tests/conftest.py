"""Tag the national-tier tests with the states they need (markers state_oh, state_va, state_tx, state_mi), so a state's build
job runs only its own: pytest -m "live and state_oh"."""
import re

import pytest

STATES = ("OH", "VA", "TX", "MI")
# tests whose state can't be read from their parameters
BY_NAME = {"test_counts_and_independent_cities_once": ("VA", "OH"), "test_statewide_impairment_table": ("OH",),
           "test_hotter_climate_uses_more_water_with_towers": ("TX", "OH"), "test_lake_source_is_great_lakes_only": ("TX",),
           "test_ohio_snapshot": ("OH",), "test_snapshot_equals_live": ("OH",), "test_michigan_point_lookup_uses_michigan_places": ("MI",),
           "test_ohio_franklin_2024": ("OH",), "test_texas_travis_2024": ("TX",), "test_virginia_loudoun_2024": ("VA",)}
POINTS = {"Columbus": "OH", "Austintown Township": "OH", "Loudoun County": "VA", "Austin": "TX"}


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
            m = re.search(r", (OH|VA|TX|MI)$", v)
            if m:
                found.add(m.group(1))
            if v in POINTS:
                found.add(POINTS[v])
    return found


def pytest_collection_modifyitems(config, items):
    for item in items:
        for st in _states(item):
            item.add_marker(getattr(pytest.mark, f"state_{st.lower()}"))
