"""A state answers the same from a snapshot or built live: both data classes offer the same methods."""
from waterledger.national.data import LiveData, SnapshotData


def public(cls):
    return {k for k, v in vars(cls).items() if callable(v) and not k.startswith("_")}


def test_live_data_has_every_method_a_snapshot_has():
    assert public(SnapshotData) - public(LiveData) == set()
