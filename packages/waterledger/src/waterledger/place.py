"""Place: any area or point Water Ledger can describe (a state, county, city, township, or a latitude and longitude).
This is broader than the Census Bureau's "place", which leaves out townships and counties."""
import re

from pydantic import BaseModel, ConfigDict

from waterledger import states


class Place(BaseModel):
    """Where. Identified by its Census GEOID; the state's provider supplies everything else (see Place.context)."""
    model_config = ConfigDict(frozen=True)
    geoid: str
    name: str
    kind: str                   # city, township, charter township, village, county, state or point
    state: str                  # postal code, e.g. "MI"
    county: str | None = None
    county_fips: str | None = None
    lat: float
    lon: float

    def context(self):
        """The public water facts around this place, by category (see waterledger.context)."""
        return states.provider(self.state).context(self)


def place(query=None, *, geoid=None, state=None, county=None, lat=None, lon=None):
    """Find a place: wl.place("Gaines charter township, MI"), wl.place("gaines", state="MI", county="Kent"),
    wl.place(geoid="2608131240"), or the government at a point: wl.place(lat=39.04, lon=-77.49)."""
    if lat is not None and lon is not None:
        from waterledger_data import census
        fips = census.state_at(lat, lon)
        if fips is None:
            raise KeyError(f"no U.S. state at {lat}, {lon}")
        st = states.state_for_fips(fips)
        if st.lower() in states.STATES and hasattr(states.provider(st).own, "place_at"):
            geoid = states.provider(st).place_at(lat, lon)
        else:
            geoid = census.place_at(lat, lon, fips)
        if geoid is None:
            raise KeyError(f"no place found at {lat}, {lon}")
    if geoid is None and query and re.fullmatch(r"\d{5,10}", str(query)):
        geoid = str(query)
    if geoid is not None:
        st = states.state_for_fips(str(geoid)[:2])
        return states.provider(st).place(str(geoid))
    m = re.fullmatch(r"\s*(.+?)\s*,\s*([A-Za-z]{2})\s*", query or "")
    name, st = (m.group(1), m.group(2)) if m else (query, state)
    if not st:
        raise ValueError('give the state: wl.place("Gaines charter township, MI") or state="MI"')
    p = states.provider(st.upper())
    return p.place(p.find(name, county))
