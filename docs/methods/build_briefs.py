"""Write a short methods brief (PDF, two pages) for each state Water Ledger covers, from that state's published snapshot, so
every count, station and report year in a brief comes from the data it describes.

    uv run python docs/methods/build_briefs.py [MI OH VA TX]      -> docs/methods/<st>.pdf

Text that is the same for every state lives here; anything state-specific is read from the snapshot (manifest, places,
supply, wastewater, receiving, climate, energy).
"""
import collections, json, os, sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, KeepTogether, Spacer, Table, TableStyle

from waterledger.national.data import fetch_snapshot

HERE = os.path.dirname(os.path.abspath(__file__))
NAMES = {"MI": "Michigan", "OH": "Ohio", "VA": "Virginia", "TX": "Texas"}
EXAMPLES = {"MI": "Gaines charter township, MI", "OH": "Columbus city, OH", "VA": "Loudoun County, VA", "TX": "Austin city, TX"}
DESIGNS = (("towers", "Cooling towers"), ("hybrid", "Hybrid"), ("assist", "Closed loop with assist"), ("dry", "Closed loop"))
EXAMPLE_MW = 300
INK, MUTED, ACCENT, LINE = colors.HexColor("#142231"), colors.HexColor("#5A6672"), colors.HexColor("#1C6B8A"), colors.HexColor("#D8DCDB")
H1 = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=17, leading=21, textColor=INK, spaceAfter=2)
SUB = ParagraphStyle("sub", fontName="Helvetica", fontSize=9, leading=12, textColor=MUTED, spaceAfter=8)
H2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=10.5, leading=13, textColor=ACCENT, spaceBefore=8, spaceAfter=3)
BODY = ParagraphStyle("body", fontName="Helvetica", fontSize=8.8, leading=11.6, textColor=INK, alignment=TA_LEFT, spaceAfter=3)
SMALL = ParagraphStyle("small", parent=BODY, fontSize=7.8, leading=10, textColor=MUTED)
CELL = ParagraphStyle("cell", parent=BODY, fontSize=8, leading=10, spaceAfter=0)
CELLB = ParagraphStyle("cellb", parent=CELL, fontName="Helvetica-Bold")


def load(state):
    folder = fetch_snapshot(state)
    j = lambda n: json.load(open(os.path.join(folder, n + ".json")))
    return folder, j("manifest"), j("places")["places"], j("supply"), j("wastewater")["plants"], j("receiving"), j("climate"), j("energy")


def table(rows, widths):
    t = Table([[Paragraph(str(c), CELLB if i == 0 else CELL) for c in r] for i, r in enumerate(rows)], colWidths=[w * inch for w in widths])
    t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, 0), 0.6, ACCENT), ("LINEBELOW", (0, 1), (-1, -1), 0.3, LINE),
                           ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]))
    return t


def pct(x):
    return f"{100 * x:.0f}%" if x is not None else "n/a"


def mgd(r):
    f = lambda x: "<0.01" if x < 0.005 else f"{x:.2f}"
    return "<0.01" if r.p90 < 0.005 else f"{f(r.p50)} ({f(r.p10)}-{f(r.p90)})"


def example(state):
    """The worked example: EXAMPLE_MW at one place in the state, every cooling design."""
    import waterledger as wl
    place = wl.place(EXAMPLES[state])
    rows = [["Design", "Withdrawn, average day", "Withdrawn, peak day", "Used up, average day", "Water from / to"]]
    for c, label in DESIGNS:
        e = wl.Site(place=place, facility=wl.DataCenter(it_mw=EXAMPLE_MW, cooling=c)).estimate()
        rows.append([label, mgd(e.water.withdrawn.avg), mgd(e.water.withdrawn.peak_day), mgd(e.water.consumed.avg),
                     f"{e.site.source} / {e.site.wastewater}"])
    return place, rows


def brief(state):
    folder, m, places, supply, plants, rec, clim, en = load(state)
    name = NAMES.get(state, state)
    mi = state == "MI"
    levels = collections.Counter(p["level"] for p in places)
    cov = (m.get("checks") or {}).get("coverage", {})
    divs = clim["divisions"]
    att = rec.get("attains") or {}
    out = os.path.join(HERE, f"{state.lower()}.pdf")
    doc = SimpleDocTemplate(out, pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch, topMargin=0.6 * inch, bottomMargin=0.6 * inch,
                            title=f"Water Ledger {name}: methods brief", author="Northline Hydrology")
    S = [Paragraph(f"Water Ledger {name}: methods brief", H1),
         Paragraph(f"Model version {m['model_version']} · data snapshot {m['date']} · waterledger.org · github.com/northlinehydrology/waterledger", SUB)]

    S += [Paragraph("What it estimates", H2),
          Paragraph(f"For any city, town, village, township or county in {name}, Water Ledger estimates how much water a data center campus "
                    "of a given size and cooling design would take, use up and send back, on an average day and on a 1-in-10-year peak day, and "
                    "sets that beside the public water system, the sewer plant, the streams downstream and the electric utility that would serve "
                    "it. It uses public data only and is a screening estimate, not a design.", BODY)]

    rows = [["Category", "Source", f"In {name}"],
            ["Places", "Census TIGERweb: county subdivisions (Michigan's cities and townships)" if mi else
             "Census TIGERweb: incorporated places; county subdivisions that are governments; counties",
             f"{len(places):,} places" + ("" if mi else ": " + "; ".join(f"{levels[k]:,} {w}" for k, w in
                                             (("place", "cities, towns and villages"), ("township", "townships"), ("county", "counties")) if levels.get(k)))],
            ["Water supply", "EPA community water system service areas, with SDWIS population and connections",
             f"{len(supply['systems']):,} systems; {pct(cov.get('water_system'))} of places have one mapped" if cov else f"{len(supply['systems']):,} systems"],
            ["Wastewater", "EPA Clean Watersheds Needs Survey 2022 (design flow) matched to ECHO (recent flow, receiving water)",
             f"{len(plants):,} plants" + (f"; {pct(cov.get('sewer_plant_within_40km'))} of places have one within 40 km" if cov else "")],
            ["Receiving waters", f"USGS Watershed Boundary Dataset; EPA ATTAINS ({att.get('organization', '')}, {att.get('cycle', '')} report)",
             f"{len(rec['downstream']):,} watersheds with a downstream path; {len(rec['reaches']):,} watersheds on those paths"],
            ["Climate", "ERA5 reanalysis (Open-Meteo), 1995-2024, at eight Michigan regions" if mi else
             "NOAA ISD station records, 1995-2024, one station per NOAA climate division; Atlas 14 design storms; Climate at a Glance rainfall",
             f"{len(divs)} {'regions' if mi else 'climate divisions'}"],
            ["Energy", "MPSC territories; EIA-861 sales and peaks" if mi else
             "HIFLD retail service territories (PNNL copy); EIA-861 sales and peaks; Siddik et al. 2024 water per kWh by grid region",
             f"{len(en['loads'])} utilities with loads; grid regions: {', '.join(sorted(en['grid_water']))}"]]
    S += [Paragraph("Data", H2), table(rows, [1.0, 3.6, 2.4])]

    S += [Paragraph("How an estimate is made", H2),
          Paragraph("<b>Cooling water.</b> Hour by hour over 30 years of weather, the campus's heat load is turned into evaporation, drift and "
                    "blowdown for each cooling design: cooling towers, hybrid (evaporative only in warm weather), closed loop with evaporative "
                    "assist on the hottest hours, and closed loop with no water for cooling. The evaporative share follows Rutberg et al. (2011); "
                    "blowdown follows the DOE FEMP water balance.", BODY),
          Paragraph("<b>Uncertainty.</b> The model runs 200 times with its 15 cooling parameters drawn from published or estimated ranges (marked [A] "
                    "where they stand in for a facility's own data). Results are the 10th, 50th and 90th percentiles; the peak day is the 90th "
                    "percentile of each year's highest day.", BODY),
          Paragraph("<b>Staff water and loop top-ups</b> are added at the campus's size (people on site, and small leaks from closed loops).", BODY),
          Paragraph("<b>Source and wastewater.</b> The campus uses the public water system mapped in the place; with none mapped, a closed "
                    "loop uses the nearest system serving over 3,300 people if it is within 10 km, and anything else uses new wells. Wastewater goes to the sewer when a plant is in reach and, for evaporative "
                    "designs, has room for the blowdown; otherwise a septic system (closed loop) or the campus's own discharge.", BODY),
          Paragraph("<b>Downstream.</b> Each place's main watershed is followed downstream (up to 25 watersheds, across state lines), with "
                    "the impairments and cleanup plans (TMDLs) EPA lists for each.", BODY)]

    if mi:
        S += [Paragraph("What Michigan adds", H2),
              Paragraph("Michigan is the full version: its own climate regions, EGLE's reported water use by county and sector, household "
                        "wells (EGLE Wellogic), designated trout streams (Michigan DNR), lake-source cooling on the Great Lakes, and Michigan's "
                        "rules (Part 327 withdrawals, Part 22 septic limits, Part 91 soil erosion, Rule 57 and temperature standards). A data "
                        "center proposal and moratorium tracker is kept by hand on waterledger.org.", BODY)]
    else:
        n = collections.Counter(v["station"] for v in divs.values())
        st = "; ".join(f"{k.title()}" + (f" ({c} divisions)" if c > 1 else "") for k, c in n.items())
        S += [Paragraph("How this differs from Michigan", H2),
              Paragraph(f"<b>Weather.</b> {name} uses NOAA station records ({st}). Michigan uses ERA5 reanalysis. For cooling towers the two "
                        "agree within about 1% in Michigan, but for hybrid and assist, which use water only on the hottest hours, station "
                        "records give higher averages (4-50% higher in southern Michigan, 2-5 times at Traverse City and Alpena), so hybrid and assist figures are not strictly comparable "
                        "across the two.", BODY),
              Paragraph("<b>Not yet included here:</b> state-reported water use by sector, household wells, coldwater streams, lake-source "
                        "cooling and state rules (\"state rules not yet reviewed\"). Utilities are listed by customers served, since the national "
                        "territory map draws many small utilities as whole counties.", BODY)]

    place, rows = example(state)
    S += [Paragraph(f"Example: {EXAMPLE_MW} MW of IT capacity in {place.name}", H2),
          Paragraph("Million gallons a day: median, with the 10th to 90th percentile range in brackets. Peak day is the "
                    "1-in-10-year highest day. \"Used up\" is water evaporated or otherwise not returned. Defaults for water source and "
                    "wastewater are filled in by the rules above (muni: public system; sewer: the nearest plant).", SMALL),
          table(rows, [1.5, 1.45, 1.45, 1.45, 1.15])]
    S[-3:] = [KeepTogether(S[-3:])]

    if cov:
        sample = (m.get("checks") or {}).get("sampled")
        errs = len((m.get("checks") or {}).get("errors", []))
        S += [Paragraph("Checks on this snapshot", H2),
              Paragraph(f"Coverage of the state's places: water system {pct(cov.get('water_system'))}, watersheds {pct(cov.get('watersheds'))}, "
                        f"utilities {pct(cov.get('utilities'))}, climate division {pct(cov.get('climate_division'))}, a sewer plant within 40 km "
                        f"{pct(cov.get('sewer_plant_within_40km'))}. {sample} places chosen at random ran through every step and cooling design "
                        f"with {errs} errors. Places with no mapped water system are mostly rural areas on private wells.", BODY)]
    elif mi:
        S += [Paragraph("Checks on this snapshot", H2),
              Paragraph("Michigan's snapshot carries the site's own files; tests confirm its answers are identical either way, and that the "
                        "shared files agree with Michigan's for places chosen at random.", BODY)]

    S += [Paragraph("Limits", H2),
          Paragraph("These are screening estimates from public data, for comparing designs and sizes before an applicant's numbers exist. "
                    "They do not replace a facility's design data, a utility's capacity analysis or a permit review. The watershed path is "
                    "followed watershed to watershed, not stream by stream. EPA assessments reflect each state's latest report. Weather is the "
                    "past 30 years.", BODY),
          Spacer(1, 6),
          Paragraph("Planning-level hydrologic assessment. Not engineering design. Built with the open waterledger Python packages "
                    f"(waterledger {m['packages']['waterledger']}); methods, parameters and sources: waterledger.org and the package "
                    "repository. Northline Hydrology.", SMALL)]
    doc.build(S)
    return out


if __name__ == "__main__":
    for st in (sys.argv[1:] or ["MI", "OH", "VA", "TX"]):
        try:
            print("wrote", brief(st.upper()))
        except Exception as e:                       # noqa: BLE001  a state whose snapshot isn't published yet
            print(f"{st}: skipped ({type(e).__name__}: {e})"[:200])
