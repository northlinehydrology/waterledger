"""ECHO's sewer plants that no survey record covers join the survey's (wastewater.echo_only)."""
from waterledger_data import wastewater as w


def _e(sid, name, lat, lon, design, status="Effective"):
    return sid, {"CWPName": name, "FacLat": str(lat), "FacLong": str(lon), "CWPTotalDesignFlowNmbr": str(design), "CWPCity": "X",
                 "CWPPermitStatusDesc": status, "PastCalYrAverageFlow": str(design / 2), "CWPMajorMinorStatusFlag": "M"}


def test_a_large_plant_next_to_a_small_one_is_added_and_a_near_twin_is_not():
    survey = [{"id": "PA0027189", "name": "LOWER ALLEN TWP STP", "lat": 40.2316, "lon": -76.8693, "design_mgd": 5.95}]
    echo = dict([_e("PA0027197", "HARRISBURG AWTF", 40.239078, -76.856111, 37.7),     # 1.5 km away, six times the size
                 _e("PA9999999", "LOWER ALLEN TWP STP", 40.2320, -76.8690, 6.0),         # the survey's plant under another number
                 _e("PA0000001", "NEW STP", 41.0, -77.0, 0.0),                          # no design flow
                 _e("PAR000001", "SOME STORMWATER", 41.5, -77.5, 1.0)])                 # a stormwater permit
    got = w.echo_only(echo, survey)
    assert [p["id"] for p in got] == ["PA0027197"] and got[0]["design_mgd"] == 37.7 and got[0]["flow_mgd"] == 18.85
