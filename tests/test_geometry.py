"""Point-in-polygon on shapely (even-odd parity over rings, so holes and multipart places work)."""
from waterledger_data.places import _inside_many

SQUARE = [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]
HOLE = [[4, 4], [6, 4], [6, 6], [4, 6], [4, 4]]
ISLAND = [[20, 20], [22, 20], [22, 22], [20, 22], [20, 20]]


def test_holes_and_parts():
    got = _inside_many([(1, 1), (5, 5), (21, 21), (15, 15)], [SQUARE, HOLE, ISLAND])
    assert list(got) == [True, False, True, False]
