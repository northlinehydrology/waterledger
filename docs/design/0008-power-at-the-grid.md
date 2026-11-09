# 0008: Power at the grid: hourly plant water, what gets built, heat and drought, on-site generators

Status: **proposed, Nov 8, 2026. Part 1 started the same day** on branch `grid-hourly`, on the proposals in decisions 1,
2 and 5 (Andrew: "let's start", without choosing among them). Decisions 3 and 4 wait for parts 4 and 2. The build
plan for part 1 is under *Part 1 as built*.

## Why

Today a campus's power plant water is its average electricity times an annual factor for one power option: the
state's mix, a grid region's average, new gas plants, the state's coal or nuclear plants, or wind and solar
(`national/power.py`, `waterledger_data.energy`). That answers "about how much", not "when", "from what", or "what
changes when the load arrives". Andrew (Nov 8, 2026) wants the power side to carry as much as the water side, for
three readers:

- **Communities:** better information on power needs, so no one is caught by surprise, including the on-site diesel
  generators that some communities are thinking of restricting. Is the fleet for outages only, or would it run on
  very hot days, and is the trade-off worth it?
- **Developers of wind, solar and storage:** grid-level context on data center proposals, beside the trackers, for
  finding places to build. Northline does not plan to publish a risk score; the data should let a reader make one.
- **Research and hiring:** grid modeling done with open tools and joined to the water side, which few people do.

## Shape: one grid model, used by every water user

- **Each user model reports its own electricity:** hourly demand, the peak day and the peak hour (model 1.9 has these
  for data centers), and its on-site generation (part 4). A battery plant or a mine does the same when it is added.
- **One grid component** turns any user's hourly electricity into water at the plants supplying it, consumed and
  withdrawn, and the fuel mix behind it. It is a model of its own, at grid level, and a BMI component like
  `CoolingWaterBmi`, so Basin Ledger can couple it to any user.
- **Studies feed it tables.** The capacity expansion runs (part 2) are a study in their own repository; the package
  reads their results as data, the way it reads `grid_water_2022.csv` today.

## Boundary

- Grid level only: balancing authority, ISO zone, state. Plant-level public records (EIA-860 and EIA-923) are inputs,
  summed by fuel and cooling type; no named plant, line or substation appears in any output.
- No power flow, interconnection or transmission studies, and nothing that is or depends on critical energy
  infrastructure information (CEII).
- On-site generators are the campus's own equipment, so they sit inside the campus boundary.
- Limits never change a number (as for water): grid stress and plant derating are context and flagged notes.

## All states

Every part names a national source, so every state gets an answer. A state can replace a layer with better data of its
own, as Michigan does elsewhere. Where a source stops (EIA-930 covers the lower 48 only), the estimate falls back to
today's annual factors and says so.

## Part 1: hourly plant water (build first)

**Question:** in the hours the campus draws the most, what is running, and what does it use in water?

- **Hourly generation by fuel:** EIA-930 (Hourly Electric Grid Monitor), every balancing authority in the lower 48,
  complete from mid-2018: coal, gas, nuclear, oil, hydro, wind, solar, other, and interchange.
- **Water by fuel and BA:** EIA-923 monthly cooling water (consumed and withdrawn) and generation by plant, with
  EIA-860 cooling types, summed by BA, fuel and month. Missing or flagged reports filled with Macknick et al. (2012),
  as the state mix does now.
- **The hour's intensity:** generation by fuel × that fuel's BA and month factor, over total generation. Imports at the
  exporting BA's mix, following de Chalendar et al. (2019) for flows between BAs [A: a first version may use the
  BA's own generation and say so].
- **The campus:** its hourly electricity × the hour's intensity, giving plant water hourly, on the average day and on
  the 1-in-10-year peak day, beside today's annual figure.
- **Average and marginal.** The hourly mix above is an average: it shares the plants running among all load. What
  responds to added load is the marginal mix, estimated from EIA-930 by the regression of Siler-Evans et al. (2012):
  the change in each fuel's generation against the change in load. Proposed: average as the main number, marginal
  beside it.
- **Weather years.** The campus runs on 30 years of ERA5; EIA-930 starts in 2018. Proposed: the intensity conditioned
  on month, hour and the BA's load percentile, from 2019 on, applied to the campus's hours by the same conditions. The
  peak day then meets the grid's own hot-day mix.
- **Closes:** the fuel shares sum to one each hour; a year of intensity × BA generation reproduces the BA's EIA-923
  water to within the reporting gaps, held by a test.

### Part 1 as built

The campus's hourly electricity exists only inside the cell runs (the cooling Monte Carlo behind each snapshot); an
estimate reads summaries. So the grid component runs inside the cell runs, and its results go into the snapshot like
the water's. Steps, each its own commit:

1. **EIA-930 hourly, by BA** (`waterledger_data.grid930`): the six-month balance files, 2019 on, cached; the adjusted
   demand and net generation by fuel for each BA, hourly in UTC.
2. **Water by BA, fuel and month** (`docs/methods/power_water/ba_fuels.py` → a package table): the plant water
   already summed for the state table, grouped by each plant's BA (EIA-860) and EIA-930's fuel classes.
3. **The hourly intensity** for each BA, 2019 on: generation by fuel × its factor, over total generation, with a test
   that a year of it reproduces the BA's plant-reported water.
4. **The grid component** (`waterledger_models.grid`): hourly MW in, hourly plant water out, with a BMI wrapper.
   Conditioning for the 30 weather years: each month and hour, the BA's intensity binned by the cell's own temperature
   that hour (quintiles within the month), fit on the years the two overlap and applied to all 30.
5. **Cell runs and the estimate:** the component in the Monte Carlo, the results in the snapshot, and a new power
   option in `est.power_plants`, with the average, the 1-in-10-year peak day and the marginal figure. Needs a rerun.

**Progress, Nov 9, 2026.** Steps 1–5 are built and tested, and step 5's rerun (model 1.11) is done in all five states.
The table is fit on 2019–2024, the years the grid's hours and the cells' weather share. Andrew kept those six years over
scaling each BA to its latest year (Nov 9): the last few years stand in for the next few [judgment]. They run about 10–16%
above 2024's plant water per MWh. Results and checks are in the methods log, Nov 9.

- Step 5: `cooling.run_location(..., grid=)` adds `grid_<BA>_<kind>_avg` and `_peak_1in10` for each BA serving a cell's
  places (`era5.cell_bas`; Michigan's cells MISO and PJM), with the table fit on the cell's own corrected temperature
  (`era5.grid_factors`; the run's local standard hours shifted to UTC). `est.grid_water` reads the place's BA. A test holds
  the plant water to the campus's electricity times the factor, average day and peak day. Gaines (shared loop, 100 MW,
  20 draws): towers 73.9 MW give 0.55 MGD consumed at MISO's plants on the average day and 0.72 on the peak day; the
  annual power options are unchanged. The grid adds about 12% to a run.

- Step 1: 67 BAs, 2019–2025. Fuel classes sum to EIA's net generation within 0.004% (MISO). EIA split hydro, solar,
  wind and storage in July 2024 and its headers carry typos; columns are matched by word.
- Step 2: the factors give back each BA's 2024 plant water within 0.4%, BPAT within 4%. Only Hawaii's two plants have no
  BA. Three plants report consumption with no withdrawal (Stanton, FL; Kings Mountain, NC; Ingleside Cogeneration,
  TX); here their withdrawal is set to at least their consumption [A]. The state table takes the same rule at the
  next release (Andrew, Nov 8: "match them"; branch `state-table-withdrawal`).
- Step 3: 2024's hours give back the large BAs' plant water within 10% (MISO 97%, PJM 100%, ERCOT 94%, SOCO 99%). The
  gap follows the difference between EIA-930's and EIA-923's generation for the BA. PSCO (+69%) and BPAT (-29%) are far
  off, from how the two surveys assign plants; flagged, not fixed.
- Step 4: `waterledger_models.grid` and `GridWaterBmi`. Fit for MISO on the Gaines cell (42.75, -85.50), 2019–2024
  (52,626 hours; the cell's ERA5 file ends Jan 1, 2025). Average: 334 gal/MWh consumed and 13,300 withdrawn in July
  hours, 259 and 10,000 in January, 312 and 12,300 over the year. Marginal: 273 and 12,200 in July, 277 and 12,600
  over the year. In MISO the plants that follow load use about the same water per MWh as the average mix; the large
  withdrawal is once-through coal and nuclear in both. Within a month and hour, neither the temperature at Gaines
  (correlation -0.15) nor MISO's own demand (-0.07) moves the mix much, and MISO's 20 highest-demand days ran 307
  gal/MWh consumed against 313 on all days. The season moves it (summer 338). So MISO's peak-day plant water comes
  from the campus's own peak power and the summer factors, not from a different mix on peak days. Small BAs may differ.

## Part 2: what gets built (its own study)

**Question:** when the region's data center pipeline arrives, which plants get built or kept running, and what do they
use in water and emit?

- **Model:** PyPSA-USA, an open capacity expansion and dispatch model of the U.S. interconnections built on PyPSA
  (Python). GenX is the alternative.
- **Scenarios:** reference load; reference plus the data center pipeline by region, from the trackers, utility filings
  and interconnection queue totals (for Michigan: DTE's 2.4 GW signed, Consumers' roughly 9 GW pipeline).
- **To the package:** a table of new and kept capacity by technology per GW of added load, by region and year. It
  becomes a power option ("what the load adds"), with its water from the technologies' factors and its emissions.
- Runs in its own repository (`grid-buildout-study`); the package gets only the curated table.

## Part 3: heat and drought on both sides (research)

**Question:** on the days a campus uses the most water and power, how much of the region's thermal capacity is limited
by warm or low cooling water?

- **Package, grid level:** for each BA, the share of thermal capacity on once-through and on recirculating cooling
  (EIA-860), and a derating curve against air and water temperature from the literature (van Vliet et al., 2012;
  Miara et al., 2017). On the campus's peak day it gives the expected derating as context.
- **Basin Ledger, basin level:** stream temperature from a coupled model, a plant's intake and discharge temperatures
  as a component, and the discharge temperature question left open in Northline's notes.

## Part 4: on-site generators

**Question:** how big is the fleet, what may it run for, and what would it burn and emit in each case?

- **Size [A]:** enough to carry the whole campus, N+1 or 2N, from the peak hour; replaced by the air permit.
- **Hours, by use:**
  - testing and maintenance, at the permit's hours or the federal limit for emergency engines (40 CFR 60 Subpart
    IIII and 63 Subpart ZZZZ, *to verify the current provisions*);
  - outages, from the utility's reliability record (EIA-861 SAIDI and SAIFI, every utility, all states);
  - **hot-day assist (what-if):** the hours the campus's load is above a firm grid supply [A], from the hourly
    electricity and the grid's hot-day stress in part 1.
- **Outputs:** run hours, fuel, and emissions from EPA engine tiers and AP-42 for each use, beside the grid's own
  emissions and water for the same hours, so the trade-off can be read both ways. Water: diesel engines use none;
  gas turbines with water injection do, and are included if a proposal uses them.
- **Trackers (Northline):** generator count, kW and permitted hours from each state's air permits, as a field on
  proposal records. Each state's permit system differs; the field is the same.

## Not in the package

Developer-facing layers (moratoria, proposals by BA and utility, load pipeline by region) stay in Northline's
trackers and data products. The package supplies the grid-level numbers they need.

## Order

1. Part 1, hourly plant water, in the grid component, for every BA EIA-930 covers.
2. Part 4, on-site generators, which uses part 1's hourly grid.
3. Part 2, in its own repository, starting with MISO.
4. Part 3, the grid-level derating first, then the Basin Ledger work.

## Decisions (Andrew, Nov 8, 2026)

1. **Average and peak.** For power, the average day and the peak day both matter, and the peak most. The average
   hourly mix is the main number, reported for the average day and the 1-in-10-year peak day; the marginal mix is
   beside it, also for both.
2. **Match the 30 weather years to the grid's hours** by month, hour and a stand-in for how loaded the grid is. As
   built, the stand-in is the temperature at the user; in MISO neither it nor MISO's demand moves the mix much
   (progress notes above).
3. **Generators: run hours and fuel, no air emissions for now.** An air quality model coupled through BMI may come
   later; none is planned.
4. **PyPSA-USA** for part 2.
5. **`waterledger-models`** holds the grid component, beside the cooling model.

## References

- de Chalendar, J. A., Taggart, J., and Benson, S. M. (2019). Tracking emissions in the US electricity system. PNAS.
- Macknick, J., et al. (2012). Operational water consumption and withdrawal factors for electricity generating
  technologies. Environmental Research Letters.
- Miara, A., et al. (2017). Climate and water resource change impacts and adaptation potential for US power supply.
  Nature Climate Change.
- Siler-Evans, K., Azevedo, I. L., and Morgan, M. G. (2012). Marginal emissions factors for the U.S. electricity
  system. Environmental Science & Technology.
- van Vliet, M. T. H., et al. (2012). Vulnerability of US and European electricity supply to climate change. Nature
  Climate Change.
- U.S. EIA: Hourly Electric Grid Monitor (EIA-930); Forms EIA-860, EIA-861 and EIA-923.
