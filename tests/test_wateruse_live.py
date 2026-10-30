"""County water use from the public sources, against the values in docs/methods/water-use-sources.md (nightly; pytest -m live)."""
import pytest

from waterledger_data import wateruse as wu

pytestmark = pytest.mark.live


@pytest.fixture(scope="module")
def usgs():
    return wu.usgs_2015()["counties"]


# Loudoun's total is 11.62 with commercial (0.05); the methods note's 11.57 left commercial out.
@pytest.mark.parametrize("fips, public, total, delivered", [("39049", 155.82, 188.31, 63.89), ("48453", 122.10, 134.11, 82.06),
                                                             ("51107", 6.86, 11.62, 27.08), ("26081", 9.01, 27.76, 31.78)])
def test_usgs_2015(usgs, fips, public, total, delivered):
    r = usgs[fips]
    assert r["mgd"]["public_supply"] == pytest.approx(public, abs=0.005) and r["mgd"]["total"] == pytest.approx(total, abs=0.005)
    assert r["delivered_to_homes_mgd"] == pytest.approx(delivered, abs=0.005)


def test_usgs_covers_every_county(usgs):
    assert len(usgs) > 3200 and usgs["26081"]["mgd"]["golf"] == 1.91 and usgs["51107"]["mgd"]["commercial"] == 0.05
    assert sum(1 for f in usgs if f.startswith("39")) == 88 and sum(1 for f in usgs if f.startswith("48")) == 254
