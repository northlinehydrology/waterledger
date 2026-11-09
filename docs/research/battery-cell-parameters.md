# Parameters for the battery cell plant model: ranges and sources

Research note, Nov 9, 2026. Sets ranges for the "Parameters to set [A]" table in
`docs/design/0009-battery-cell-plants.md`. Builds on `docs/research/battery-plant-water.md` (plant water figures, EA
page numbers) and does not repeat it. Public sources only. No code.

Conventions:

- **kWh/kWh**: kWh of site energy (electricity plus fuel, fuel at the meter, higher heating value unless stated) per
  kWh of cell capacity produced. 1 MJ = 0.2778 kWh. 1 MMBtu = 293.07 kWh.
- **Type** of each value: *measured* (metered at a plant), *permit/projection* (applicant or permit figure before or
  without metering), *model* (process or factory model), *estimate* (my derivation from the cited inputs, marked [A]).
- **UNVERIFIED**: not checked against the primary document in this session.
- A plant of 1 GWh/yr at full output makes 114.2 kWh of cells per hour. Lansing (43.75 GWh/yr) makes 4,994 kWh/h.
- Page or table numbers refer to the source's printed numbering.

## 1. Site energy per kWh of cells

### Evidence

| Source | Plant / scope | kWh/kWh | Electricity / fuel | Type |
|---|---|---|---|---|
| Kuki et al. 2025, Table 1 and §3.1.1 | CATL Debrecen, 40 GWh/yr NMC811, includes offices ("social") | **34.6** | 533 GWh elec + 90e6 m³ gas (849.6 GWh at 9.44 kWh/m³) | permit projection |
| Kuki et al. 2025, Table 1 and §3.2.1 | Samsung SDI Göd, 26 GWh/yr (capacity derived from 130,900 t/yr at 200 Wh/kg) | **28.3** | 497 GWh elec + ~26e6 m³ gas (245 GWh) | annual energy report (measured, but divided by capacity, not output) |
| Kuki et al. 2025, Table 1 and §3.3.1 | SK On Iváncsa, 30 GWh/yr NMC811 | **≥ 29.4** (gas only) | 93.6e6 m³ gas; electricity not found | permit projection |
| Degen et al. 2023, Fig. 3 and Source Data Fig. 3 | Factory model, today's technology, 60 expert interviews; excludes building HVAC and offices | **20.3** (NMC900) to **22.4** (NMC811), **26.0** (NMC622), **37.5** (LFP) | NMC811: 10.9 elec + 11.6 gas | model |
| UKBIC 2022, §2.5 | Pilot measurements scaled to gigafactory, cylindrical NMC cell | **29** | not split | model from measured pilot equipment |
| Dai, Kelly, Gaines, Wang 2019, §3.2.2 (GREET) | Chinese 2 GWh/yr NMC line, at 75% of capacity | **47** (170 MJ) | 30 MJ elec (8.3 kWh) + 140 MJ steam (38.9 kWh) | manufacturer estimate |
| Kallitsis meta-analysis, as cited by Kuki et al. 2025 §1 | Five studies of plants > 1 GWh/yr, NMC333 or later | **30-50** | — | review (UNVERIFIED, read through Kuki) |
| Kurland 2020, abstract | Two large plants (Tesla Nevada from utility taxes; Northvolt EIA) | **50-65** electricity | electricity only | estimate from public data |
| Northvolt Ett EIA, via Kurland 2020 search snippet | First 8 GWh/yr line, 400 GWh/yr electricity | **50** (all-electric) | 100% electricity | permit projection (UNVERIFIED) |
| Ultium Lansing EA (DOE/EA-2189-S1), §3.11.3 and Table 2 | 43.75 GWh/yr | **~20-34** (derived, below) | see §2 | estimate from EA emissions [A] |

Derivation from the Lansing EA. The EA gives 320,870 tons/yr of CO2e from grid electricity and 238,355 tons/yr from
natural gas (§3.11.3, p. 31). The gas figure matches the facility's potential to emit (238,901 tpy CO2e, Table 2, p.
13), so it is permitted burner capacity running all year, an upper bound. At 53.11 kg CO2e per MMBtu (40 CFR 98
Table C-1 and C-2 factors for natural gas, my sum), 216,233 t is 4.07 million MMBtu/yr, or 136 MW of firing capacity
(27.3 kWh/kWh if fired all year). Burners in a plant like this fire at perhaps 30-60% of capacity on average [A], so
**8-16 kWh/kWh of gas**. The EA does not state the grid factor. At 800-1,250 lb CO2e/MWh [A], 291,088 t is 513-802
GWh/yr, or **11.7-18.3 kWh/kWh of electricity**. The Spring Hill EA (DOE/EA-2189, p. 28) gives the same electricity
figure, 320,870 tpy, so it is a company estimate used for more than one plant.

Two upper checks on electricity:

- **BlueOval SK, Glendale (82 GWh/yr).** Kentucky Utilities' special contract provides 140 MW firm in year one and
  **260 MW firm** after that (KY PSC Case 2023-00123, Application ¶16, Apr 14, 2023). That is 3.2 MW per GWh/yr. Even
  if the plant drew the full firm demand all year, electricity would be at most 27.8 kWh/kWh. At an average of 80-95%
  of firm demand [A] it is 22-26 kWh/kWh. A search summary says the contract expects monthly load factors above 95%
  (UNVERIFIED, not found in the application text).
- **Panasonic, De Soto (32 GWh/yr).** Evergy testimony to the Kansas Corporation Commission puts the plant at 200-250
  MW at full output (Kansas City Star via Yahoo, 2023; UNVERIFIED, secondary). That is 6.3-7.8 MW per GWh/yr, which
  only fits a plant with much of its heat electric.

### Reading

- Gas-heated plants of the current generation cluster at **28-35 kWh/kWh**: Kuki's three plants, UKBIC's 29, and the
  Lansing derivation.
- Degen's 22 kWh/kWh for NMC811 leaves out building HVAC and offices. It is a floor for a real plant.
- Dai's 47 kWh/kWh was measured at 75% of capacity on a 2016 line. Kurland's 50-65 includes all-electric heat.
  Both show where the upper end comes from: older lines, low utilization and electric heating.
- **Chemistry.** Degen finds the same energy per m² of electrode for every lithium-ion chemistry (5.2 kWh per m²),
  so energy per kWh scales with the inverse of areal energy: LFP at 68.8 Wh/m² of stack against NMC811 at 114.8 needs
  1.67 times as much (37.5 against 22.4). Plants making large LFP prismatic cells with thicker electrodes will narrow
  that gap. 0009 records chemistry without effect for now; if it is used later, a factor of about 1.3-1.7 for LFP
  over NMC is the evidence.
- **Utilization.** Energy per kWh rises when a plant runs below nameplate, because dry rooms, HVAC and building loads
  run regardless of output (UKBIC §2.5: dry room energy "is not directly linked to cell production throughput"; Dai
  §3.2.2; Ellingsen's high values came from an under-used plant). In Degen's model, dry rooms and material handling
  are 30% of energy. The model should split plant energy into a **fixed share φ = 0.3-0.5 (central 0.4)** [A] that
  does not scale with output and a variable share that does.

### Proposed

| Parameter | Low | Central | High | Basis | Type |
|---|---|---|---|---|---|
| Site energy, NMC/NCA, at full output | 25 | **32** | 45 | Kuki (28.3-34.6), UKBIC (29), Lansing EA derivation (20-34); Degen (22) as a floor; Dai (47) as the high end | permit, model, estimate |
| LFP multiplier (only if chemistry is used) | 1.2 | 1.4 | 1.7 | Degen Fig. 3 (1.67); narrowed for thicker LFP electrodes [A] | model, estimate |
| Fixed share of energy at part load, φ | 0.3 | 0.4 | 0.5 | Degen source data (dry rooms + material handling 30%); UKBIC §2.5 | model, estimate |

## 2. Electricity and fuel

### Evidence

| Source | Electricity share of site energy | What burns fuel |
|---|---|---|
| Degen et al. 2023, Source Data Fig. 3 (all LIB chemistries) | **0.48** | Coater dryers (2 × 825 kW gas per line), vacuum dryers (2 × 210 kW), dry room desiccant regeneration (913 kW), high-temperature aging (40 kW). Of the gas: dryers 57%, dry rooms 41%, aging 2% |
| Kuki et al. 2025, CATL Debrecen | **0.39** (533 of 1,383 GWh) | not stated |
| Kuki et al. 2025, Samsung SDI Göd | **0.67** (497 of 742 GWh) | not stated |
| Dai et al. 2019 (GREET), Chinese line | **0.18** (30 of 170 MJ) | Steam for dry room dehumidification (56-71 MJ/kWh) and electrode drying (56-71 MJ/kWh) |
| Lansing EA (derived, §1) | **0.42-0.70** (11.7-18.3 elec against 8-16 gas) [A] | "air-handling units and boilers" (p. 13) |
| SK Battery America, Bartow Co., GA air permit narrative (App. 28655, Dec 22, 2022, pp. 1 and 3) | — | Twelve hot oil heaters for the cathode and anode dryers (6 × 35.3 and 6 × 30.5 MMBtu/h = 394.8 MMBtu/h, 116 MW); six boilers for "comfort heat and process heat" (6 × 50.7 = 304.2 MMBtu/h, 89 MW). Total 699 MMBtu/h (205 MW); one boiler and two heaters are standby, so 582.5 MMBtu/h (171 MW) runs. At a stated ~35 GWh/yr (UNVERIFIED): 4.9 MW of running gas capacity per GWh/yr |
| KORE Power EA (DOE/EA-2222), Table 6 (p. 37) and fn. 7 (p. 25) | — | HVAC only: 38 dehumidification units and 62 rooftop units, 19.3 MMBtu/h of gas in total |
| Northvolt Ett EIA (via Kurland) | **1.0** | none; all-electric (UNVERIFIED) |

### Reading

The U.S. EA plants burn gas for three things: dryer heat (through hot oil heaters), desiccant regeneration and
process steam (through boilers), and space and make-up air heating in winter. Lansing's permitted gas capacity per
GWh/yr is 2.6 times Spring Hill's (136 MW for 43.75 GWh/yr against 52 MW for 35-50 GWh/yr), and the EA puts most of
the gas in "air-handling units and boilers". That points to winter heating of make-up air in Michigan. So the fuel
share is partly a weather term. The heating fuel does not reach the cooling water (§3).

### Proposed

| Parameter | Low | Central | High | Basis | Type |
|---|---|---|---|---|---|
| Electricity share of site energy (gas-heated plant) | 0.35 | **0.50** | 0.70 | Degen 0.48; Kuki 0.39 and 0.67; Lansing 0.42-0.70 [A] | model, permit, estimate |
| All-electric variant (heat pumps, electric heaters) | — | 1.0 | — | Northvolt Ett; Panasonic De Soto's demand (UNVERIFIED) | scenario |

Dai's 0.18 is left out of the range: it counts steam at its delivered heat and comes from a 2016 line with a heavy
steam dry room. It shows that the share can be low.

## 3. Energy by step, and how much reaches the cooling water

### Breakdown by step

| Step | Degen NMC811 (kWh/kWh, share) | Degen LFP | UKBIC gigafactory scale | Dai / GREET |
|---|---|---|---|---|
| Electrode coating and drying, vacuum drying | 7.17 (32%) | 11.98 (32%) | 24% | 15.6-19.7 kWh steam (33-42%) |
| Dry rooms | 5.58 (25%): 0.85 elec + 4.74 gas | 9.32 (25%) | 34% | 1.9-7.2 elec + 15.6-19.7 steam (37-57%) |
| Formation, aging, end-of-line testing | 5.91 (26%), all electric except 0.21 gas for high-temperature aging | 9.87 (26%) | 24% | 1.1 (charging only) |
| Other (mixing, calendering, slitting, assembly, cell washing, material handling) | 3.79 (17%) | 6.30 (17%) | 17% (by difference) | "negligible" |
| Total | 22.45 | 37.46 | 29 | 47 |

Sources: Degen Source Data Fig. 3, per-chemistry sheets (cell-specific electric and gas consumption columns); UKBIC
white paper §2.5 and §3.1-3.3; Dai et al. 2019 §3.2.2. Electrode drying, dry rooms and formation together are 76-83%
of plant energy in every source.

### Where each step's heat goes

All site energy leaves as heat: to the cooling water (towers or dry coolers), to exhaust air, to flue gas, or through
the building envelope. The product carries away less than 1 kWh per kWh (cells ship partly charged). The split below
is my estimate from how each system works [A]. No source measures it.

| Step | Energy form | Where the heat goes | Share to cooling water |
|---|---|---|---|
| Formation, aging, testing | electricity | Charger and cell losses into conditioned rooms, removed by air handler coils on chilled water | 0.85-0.95 |
| Other process electricity (drives, compressed air, vacuum pumps, lighting, offices) | electricity | Mostly room loads on chilled water; air compressors water-cooled; some leaves in general exhaust | 0.7-0.9 |
| HVAC and dry-room fans, pumps | electricity | Into the air streams the coils cool | 0.7-0.9 |
| Chiller compressors | electricity | Rejected with the chilled load (water-cooled chillers) | 1.0 |
| Cathode (NMP) dryers | fuel via hot oil | 10-20% flue loss. Exhaust passes heat recovery, then cooling and chilled water coils that condense NMP (SK Bartow: "emissions from the dryers are collected by scrubbers for NMP recovery") | 0.4-0.6 |
| Anode (water) dryers | fuel via hot oil | 10-20% flue loss; humid exhaust vented, partly through heat recovery | 0.05-0.2 |
| Dry room desiccant regeneration | steam, hot water or gas | Regeneration air leaves hot and wet to outdoors; 10-20% carries over into the process air and is removed by the post-cooling coil | 0.1-0.2 |
| Space and make-up air heating, high-temperature aging | fuel | Leaves through envelope and exhaust in the heating season | 0 |

Central case at 32 kWh/kWh and an electricity share of 0.5 [A]:

| Part | kWh/kWh | Share to water | To water |
|---|---|---|---|
| Formation, aging, testing | 4.5 | 0.9 | 4.05 |
| Other process electricity | 6.5 | 0.8 | 5.20 |
| HVAC fans, pumps | 3.0 | 0.8 | 2.40 |
| Chiller compressors | 2.0 | 1.0 | 2.00 |
| Cathode dryers | 4.6 | 0.5 | 2.30 |
| Anode dryers | 4.6 | 0.1 | 0.46 |
| Desiccant regeneration | 5.2 | 0.15 | 0.78 |
| Heating, other fuel | 1.6 | 0 | 0 |
| **Total** | **32.0** | **0.54** | **17.2** |

Three checks on the share, top-down:

- **Lansing EA consumption.** 0.94-1.14 MGD consumed, less ~0.08 MGD of process and staff consumption (§6, §7),
  leaves 0.86-1.06 MGD of tower evaporation. At 1.48 L per kWh of heat that is 91-113 MW, or 18.3-22.6 kWh of heat
  per kWh of cells: a share of **0.57-0.71** at 32 kWh/kWh (0.52-0.65 at 35).
- **CATL Debrecen.** 27.9 L/kWh of water in total at 34.6 kWh/kWh (Kuki Table 1) allows at most 0.54 even if every
  litre were tower evaporation. Debrecen is the low end, or uses dry or hybrid cooling for part of its load.
- **Tower sizing at SK Bartow.** 310,100 gpm of circulation (permit narrative p. 4) at a 10 °F range is 454 MW of
  rejection capacity, 13 MW per GWh/yr at a stated 35 GWh/yr. The central case averages 2.1 MW per GWh/yr. Towers are
  sized for the design day, all burners firing and spare cells. The ratio of 6 is large, and Bartow's 3.6 MGD (DRI,
  UNVERIFIED) is also three times the EA band; Bartow stays an outlier on both counts.

### Proposed

| Parameter | Low | Central | High | Basis | Type |
|---|---|---|---|---|---|
| Share of site energy to the cooling water, annual average, including chiller compressor work | 0.45 | **0.60** | 0.75 | Bottom-up 0.54 [A]; Lansing EA consumption 0.57-0.71; CATL Debrecen ≤ 0.54 | estimate |

The central value sits between the bottom-up estimate and the EA. 0009's 0.65 is inside the range.

**Accounting rule for the code.** Chiller compressor work is part of the plant's electricity. If the model adds it
again through heat rejected = load × (1 + 1/COP), the share must be applied to plant energy net of chiller work. In
the central case, about 0.75 of the heat to water passes through chillers [A] (the rest is direct process cooling
water: air compressors, hydraulic units, the first NMP coils), and the chiller work is about 2 kWh/kWh. So the share of
non-chiller energy that becomes chilled or process-water load is about 0.53 [A], and the (1 + 1/COP) term brings it
back to 0.60. Either way works; the code must use one and say which.

## 4. Dry rooms and outdoor air

### Evidence

| Item | Value | Source | Type |
|---|---|---|---|
| Room dew point, cell assembly | -35 to -45 °C, -40 °C typical | Munters (Charged EVs, sponsored, Nov 3, 2021); Bry-Air (Volta Foundation, Oct 1, 2024: -40 °F, which is -40 °C) | vendor |
| Electrolyte filling | -50 °C | UKBIC 2022, Table 2.2 | pilot plant |
| Electrode and assembly rooms in a zoned plant | -30 °C (assembly), -40 °C (fill) | Bry-Air, Volta Foundation 2024, 55,000 ft² pilot line | vendor |
| Supply air dew point for a -40 °C room | -60 °C | Degen et al. 2023, Fig. 2 note and Supp. Table 1 | model |
| Energy of a -60 °C room against a -40 °C room | 1.73 times | Degen Source Data Fig. 2 | expert estimate |
| Dry room floor area | 957 m² per line of 0.8-1.2 GWh/yr | Degen Source Data Fig. 3, "Dry Rooms" sheet (footprint from Degen and Krätzig 2023) | model |
| Dry room volume and power | 16,000 m³ and ~400 kW for 100,000 packs/yr of 10 kWh (1 GWh/yr), i.e. 3.5 kWh/kWh | Ahmed, Nelson, Dees 2016 (J. Power Sources 326:490-497), abstract; basis from DOE VTO 2016 merit review slides (UNVERIFIED, search summary) | model |
| Make-up air pre-cooled ("quenched") to about 6 °C ahead of the desiccant wheel | — | Ahmed et al. 2016, as cited by a 2021 study (UNVERIFIED, search summary) | model |
| Dry room energy, measured line | 7-26 MJ electricity + 56-71 MJ steam per kWh of cells, at 75% of capacity, "depending on the climatic conditions"; electricity "predominantly" for 11 dehumidifiers and four industrial chillers | Dai et al. 2019 §3.2.2 | manufacturer estimate |
| Main moisture source | people (1,500-2,000 grains/h each, about 0.1 kg/h) | UKBIC Table 3.3; Bry-Air, Volta Foundation 2024 | pilot, vendor |
| Rotor split | about 3/4 process air, 1/4 regeneration air | Munters, Charged EVs 2021 | vendor |
| HVAC units, KORE Phase 1 (6 GWh/yr) or full build (12) | 38 dehumidification units, 62 rooftop units | DOE/EA-2222, fn. 7, p. 25 | projection |

Nothing found states a battery plant's outdoor air flow, its make-up air per GWh/yr, or regeneration heat per kg of
water. The ASHRAE Handbook chapter on desiccant dehumidification and the vendors' design guides were not available
in this session.

### Outdoor air share of the design cooling load: estimate [A]

The outdoor-air load is the chilled-water load from cooling and drying make-up air at the design condition. Two
streams carry it:

- Dry room make-up air (pressurization, exhaust, door losses). It is pre-cooled, dried by the desiccant wheel, and
  post-cooled. The heat of adsorption appears as sensible heat in the process air, so the chilled-water load is about
  the enthalpy drop from outdoor air to the dry supply air: about 68 kJ/kg at a Michigan 1% dehumidification
  condition [A] down to about 18 kJ/kg (18 °C, -40 °C dew point), so 50 kJ/kg, plus regeneration carry-over.
- Make-up air for the other conditioned areas (electrode, formation, aging; SSOE's brochure lists humidity control and
  make-up air handling for each). Cooled to about 12 °C saturated (34 kJ/kg): about 34 kJ/kg.

Central flows of 3,000 m³/h (dry rooms) and 12,000 m³/h (other areas) per GWh/yr [A] give 54 + 134 = 188 kW of
chilled load per GWh/yr at design, 222 kW at the tower with a COP of 5.5. The process heat to the towers at full
output is 0.60 × 32 × 114.2 = 2,190 kW per GWh/yr. The outdoor-air share of the design load is then 222 / 2,412 =
**0.09**. Flows of 5,000-40,000 m³/h per GWh/yr give 0.03-0.22.

Two checks:

- **Spring Hill's peak-to-average ratio of 1.32** (DOE/EA-2189, p. 14) bounds the share from above. If the whole
  ratio came from the outdoor-air load and none from the tower's higher summer evaporation or a design margin, the
  share at design would be about 0.25-0.30. Part of the ratio is the tower and part is margin, so the share is below
  that.
- **Dai's dry room electricity of 7-26 MJ/kWh with climate** is a swing of 5.3 kWh of electricity per kWh of cells,
  on a line in a humid subtropical climate (UNVERIFIED location). At a low-temperature chiller COP of about 4 that
  is a swing of about 20 kWh of cooling per kWh, large next to 17 kWh of process heat to water. It argues for the
  upper half of the range in humid climates, or it includes dehumidifier fans and regeneration blowers that do not
  scale this way. It cannot be separated with what is published.

### Proposed

| Parameter | Low | Central | High | Basis | Type |
|---|---|---|---|---|---|
| Outdoor-air share of the design-day cooling load | 0.05 | **0.12** | 0.30 | Estimate above (0.03-0.22); Spring Hill 1.32 as an upper bound; Dai's climate swing argues against the lowest values | estimate |
| Room dew point (recorded, for a later dry-room term) | -45 °C | -40 °C | -35 °C | vendors, Degen, UKBIC | vendor, model |
| Dry room energy, share of plant energy | 0.20 | 0.30 | 0.45 | Degen 25%, UKBIC 34%, Dai 37-57% | model, measured line |

This narrows 0009's starting range of 0.1-0.4. In the heating season the same air is heated by gas (§2), which does
not reach the cooling water.

## 5. Chillers and chilled water

No public source gives a battery plant's measured chiller COP. The values below are handbook and code minimums plus
the temperatures the processes need.

| Item | Value | Source | Type |
|---|---|---|---|
| Low-temperature chilled water for dry-room pre-cooling and NMP condensers | about 4-6 °C supply (air quenched to about 6 °C) | Ahmed et al. 2016 via secondary citation (UNVERIFIED); NMP condensing practice [A] | model, estimate |
| Medium-temperature chilled water (formation rooms, process, comfort) | 7-14 °C supply [A] | common plant practice | estimate |
| Water-cooled centrifugal chiller, full-load minimum | about 0.56-0.61 kW/ton (COP 5.8-6.3) at 6.7 °C leaving water | ASHRAE 90.1-2019 Table 6.8.1-3, Path A (UNVERIFIED, from memory; check before citing) | code minimum |
| Air-cooled chiller, full-load minimum | about EER 10.1 (COP 3.0) | same (UNVERIFIED) | code minimum |
| Plants in the record | "four industrial chillers" (Dai's line); "closed-loop chiller water" and a chiller yard (KORE, which reads as air-cooled); "descaling chillers" as a water saving (LGES ESG 2024) | as cited | — |

### Proposed

| Parameter | Low | Central | High | Basis | Type |
|---|---|---|---|---|---|
| Water-cooled chiller COP, annual average, mix of low- and medium-temperature loops | 4.5 | **5.5** | 7.0 | Code minimums at 6.7 °C; lower for 4-5 °C water; higher at part load and with cool condenser water | estimate |
| Air-cooled chiller COP (dry design), annual average | 2.5 | **3.2** | 4.0 | Code minimum about 3.0; higher in cool weather | estimate |
| Share of heat to water that passes through chillers | 0.6 | 0.75 | 0.85 | §3 [A] | estimate |

The data center model's COP ranges can be shared if they cover these values. The low-temperature loop for dry rooms
is the difference from data centers, whose chilled water runs warmer.

## 6. Process water by stream

### Evidence

| Stream | Figure | Per kWh of cells | Source | Type |
|---|---|---|---|---|
| Anode slurry solids | 42% by mass (cathode 76%) | water/solids = 1.38 | UKBIC 2022, Table 2.1 | pilot plant |
| Anode solids per kWh | — | about 1.0-1.2 kg/kWh NMC, 1.3-1.5 LFP [A] | cell design order of magnitude (BatPaC class; not checked) | estimate |
| Anode slurry water, evaporated in the dryers | — | **1.0-2.0 L/kWh**, central 1.5 [A] | from the two rows above; industrial slurries at 45-55% solids give the low end | estimate |
| NMP use | 0.51-0.56 kg/kWh (Samsung Göd, SK Iváncsa); CATL: NMP "recovered within the factory", 2,000 t/yr make-up for 40 GWh/yr (0.05 kg/kWh) | — | Kuki et al. 2025, Table 1 | permit |
| NMP scrap leaving by tanker, BlueOval City (45 GWh/yr) | 144,000,000 lb/yr | 1.45 kg/kWh of NMP-water mixture; at ~0.5 kg/kWh of NMP, about **0.95 L/kWh of water** [A] | DOE/EA-2201, Table 6 | projection, estimate |
| Used NMP and process water trucked off site, StarPlus Kokomo (67 GWh/yr) | used NMP 1,280,320 gal/yr; process contact wastewater 7,464,250 gal/yr; "salt water" 1,972,825 gal/yr; washing fluid 16,460 gal/yr | used NMP 0.07 L/kWh; trucked water 0.53 L/kWh | DOE/EA-2263, Table 4, p. 23 | projection |
| A123 (2010, LFP powder plus cells) | NMP scrubber 11,232 gpd; process (99.9% water from solvent recovery bottoms) 3,034 gpd; boiler blowdown 15,726 gpd; tower blowdown 6,155 gpd | — | DOE/EA-1690, Table 2-5 | projection |
| Reverse osmosis recovery | 65-80% [A] | reject 0.25-0.54 L per L of permeate | common two-pass RO/EDI practice; no battery-plant source found | estimate |
| Boiler make-up | steam for regeneration and process heat; dryers use hot oil (SK Bartow) | 0.2-2.0 L/kWh [A] | §3 boiler fuel (~5-7 kWh/kWh) at 80-90% condensate return; hot-water boilers need almost none | estimate |

The NMP stream's water goes one of two ways. Where recovered NMP-water is shipped for purification (SK Bartow, the
permit narrative p. 1; BlueOval City), its water leaves the watershed: consumption. Where the plant distills NMP on
site (A123's solvent recovery bottoms), the water goes to the sewer or, at StarPlus, by truck. StarPlus's trucked
streams (0.53 L/kWh) and BlueOval City's NMP scrap (~0.95 L/kWh) bracket the shipped water.

### Proposed (per kWh of cells at full output)

| Stream | Low | Central | High | Fate | Type |
|---|---|---|---|---|---|
| Anode slurry water (purified) | 1.0 | **1.5** | 2.0 | consumed (evaporated in dryers) | estimate |
| Water shipped off site in NMP or trucked process water | 0 | **0.5** | 1.0 | consumed for the watershed | projection, estimate |
| Other purified water (cleaning, scrubbers, labs) | 0.2 | **0.5** | 1.0 | returned to sewer | estimate |
| RO recovery (permeate / feed) | 0.65 | **0.75** | 0.80 | reject returned | estimate |
| Boiler make-up | 0.2 | **0.7** | 2.0 | ~0.2 returned as blowdown, rest lost as steam | estimate |

Central totals: withdrawal 4.0 L/kWh (RO feed 3.33 + boiler 0.7), consumption 2.5, return 1.5. That is about 2,900
gpd per GWh/yr, under a tenth of the plant total. Process water matters for discharge quality more than for volume.

## 7. Staff and utilization

### Staff per GWh/yr (EA employment at full production)

| Plant | Employees | GWh/yr | Per GWh/yr | Source |
|---|---|---|---|---|
| Ultium Lansing | 1,522 (435 per shift × 3 + 217 office on shift 1; 3 shifts, 6 days) | 43.75 | 35 | DOE/EA-2189-S1 §2.2.2, p. 9 |
| Ultium Spring Hill | 1,300 (~400 per shift) | 35-50 (UNVERIFIED) | 26-37 | DOE/EA-2189 §2.2.2, p. 9 |
| BlueOval City | 2,200 hourly + 300 salaried | 45 | 56 | DOE/EA-2201, p. 14 |
| BlueOval SK, Glendale | 4,400 hourly + 600 salaried | 82 | 61 | DOE/EA-2201, p. 18 |
| StarPlus Kokomo | 2,600 hourly + 900 salaried (4 shifts) | 67 | 52 | DOE/EA-2263, p. 9 |
| KORE Buckeye | 1,500 (Phase 1) | 6 (or 12) | 125-250 | DOE/EA-2222, p. 10 |

Large plants: 26-61 per GWh/yr. Small plants run higher. The staff water per person can share the data center
model's range; for reference, sanitary design guides use roughly 15-35 gal per employee per shift for factories,
excluding process water (Ten States Standards, UNVERIFIED). At 25 gal per employee and 6 of 7 days on site, Lansing's
staff water is 1,522 × 6/7 × 25 = 32,600 gpd.

### Utilization (output ÷ nameplate) in early years

| Evidence | Value | Source |
|---|---|---|
| Lansing staffing ramp | 7% (Q1 2023) to 100% (Q1 2025), quarter by quarter | DOE/EA-2189-S1, Table 1 |
| LG Energy Solution, average plant utilization | 73.6% (2022), 69.3% (2023), 57.8% (2024), 51.3% (H1 2025) | Korea Times, Aug 15, 2025, from company semiannual reports |
| SK On | 87.7% (2023), 43.6% (2024), 52.2% (H1 2025) | same |
| Samsung SDI | 58% (2024, small cells); 44% (H1 2025, small cells) | same |
| Korean makers, full year 2025 | ~48-50% (LGES 47.6%, SK On 48.7%, Samsung SDI ~50%) | SMM analysis of the annual reports (UNVERIFIED, secondary) |
| Ultium Lordstown and Spring Hill | cell production paused from January 2026, planned restart mid-2026, Lordstown on one shift | GM statements reported Oct 2025 (Tribune Chronicle; Yahoo/Tennessean) |
| Ultium Lansing | built for EV cells, sold to LGES before reaching full EV output (per 0009) | — |

### Proposed

| Parameter | Low | Central | High | Basis | Type |
|---|---|---|---|---|---|
| Staff per GWh/yr (large plants) | 25 | **45** | 65 | EA employment, five large plants | projection |
| Utilization, headline | — | **1.0** | — | EA convention (0009 decision 2) | — |
| Utilization, sampled range for running plants | 0.4 | 0.65 | 1.0 | Korean company-wide 0.44-0.88 in 2022-2025; ramp-up schedules; pauses | reported |

The sampled low end is 0.4 rather than 0.6 in 0009: company-wide utilization of 44-52% was reported for 2024-2025.
With the fixed share φ from §1, a plant at 0.5 utilization uses 70% of its full-output energy, not 50%.

## 8. Energy balance check at Lansing

Central values: 43.75 GWh/yr at full output; 32 kWh/kWh; share to water 0.60; outdoor-air load adds 3% to the annual
mean heat in Michigan (the 0.12 design share times about a quarter of design load on average over the cooling season,
[A]); evaporation 1.48 L per kWh of heat (all heat latent, the upper bound; the package's Rutberg ratio lowers this);
process water as in §6; staff as in §7.

| Step | Arithmetic | Value |
|---|---|---|
| Cells per hour | 43.75e6 ÷ 8,760 | 4,994 kWh/h |
| Site energy | 4,994 × 32 | 159.8 MW |
| Heat to the cooling water | 159.8 × 0.60 = 95.9; × 1.03 | 98.8 MW |
| Evaporation | 98,800 kWh/h × 1.48 L × 24 h = 3,509 m³/d | 0.927 MGD |
| Blowdown + drift, 5 cycles | 0.927 ÷ 4 | 0.232 MGD (4 cycles 0.309; 6 cycles 0.185) |
| Process water withdrawn | 43.75e6 × 4.03 L ÷ 365 = 483 m³/d | 0.128 MGD (consumed 0.079, returned 0.048) |
| Staff water | 32,600 gpd, 10% consumed | 0.033 MGD |
| **Withdrawn, 5 cycles** | 0.927 + 0.232 + 0.128 + 0.033 | **1.32 MGD** (4 cycles 1.40; 6 cycles 1.27) |
| **Consumed** | 0.927 + 0.079 + 0.003 | **1.01 MGD, 77%** |
| **Discharged** | 0.232 + 0.048 + 0.030 | **0.31 MGD** |
| EA (DOE/EA-2189-S1, p. 19) | — | 1.5-1.7 withdrawn, 0.94-1.14 consumed (63-67%), 0.56 discharged |

**Result.** Consumption lands inside the EA's range. Withdrawal at 4-6 cycles is 1.27-1.40 MGD, 7-25% below the EA,
and the discharge is about half the EA's. Withdrawal and discharge match the EA almost exactly at **3 cycles**: 1.55
MGD withdrawn, 1.01 consumed (65%), 0.54 discharged. The EA's own numbers imply about 3 cycles: 0.56 MGD discharged
less 0.08 of process and staff return leaves 0.48 MGD of blowdown against about 0.96 of evaporation, C = 1 + 0.96 ÷
0.48 = 3.0. Lansing's supply is Saginaw Formation groundwater bought from Lansing BWL; why the design assumes 3 cycles
(hardness, silica, or a conservative estimate) is not stated.

So the energy balance closes on the EA's consumption with central values, and the gap in withdrawal is the cycles of
concentration, not the heat. Two cautions:

- With the package's evaporative ratio below 1 (Rutberg et al. 2011), evaporation per kWh of heat drops by perhaps
  10-20% in Michigan, and consumption would fall to about 0.85 MGD, below the EA range. Matching it would then need
  the upper half of the energy or share ranges (for example 38 kWh/kWh at a share of 0.62 gives 1.58 MGD withdrawn at
  5 cycles with a ratio of 1).
- The EA figures are pre-construction projections, probably sized with margin. They are a check, not a target (0009).

The same central values at BlueOval City's 45 GWh/yr give about 1.36 MGD at 5 cycles against the EA's 1.2 MGD. The
central case sits between BlueOval City and Lansing, at 29,000-35,000 gpd per GWh/yr across 6-3 cycles, inside the
EA band of 27,000-39,000.

## 9. All proposed ranges

| Parameter | Low | Central | High | Main source | Type |
|---|---|---|---|---|---|
| Site energy, NMC/NCA (kWh/kWh) | 25 | 32 | 45 | Kuki et al. 2025 Table 1; UKBIC 2022; Lansing EA (derived) | permit, model, estimate |
| LFP multiplier (optional) | 1.2 | 1.4 | 1.7 | Degen et al. 2023 Fig. 3 | model |
| Fixed share of energy at part load φ | 0.3 | 0.4 | 0.5 | Degen source data; UKBIC | model, estimate |
| Electricity share of site energy | 0.35 | 0.50 | 0.70 | Degen 0.48; Kuki 0.39/0.67 | model, permit |
| Share of site energy to cooling water (annual mean, incl. chiller work) | 0.45 | 0.60 | 0.75 | Bottom-up §3; Lansing EA consumption | estimate |
| Outdoor-air share of design cooling load | 0.05 | 0.12 | 0.30 | Psychrometric estimate §4; Spring Hill peak ratio | estimate |
| Room dew point (recorded) | -45 °C | -40 °C | -35 °C | Munters, Bry-Air, Degen | vendor, model |
| Water-cooled chiller COP | 4.5 | 5.5 | 7.0 | ASHRAE 90.1 minimums (UNVERIFIED), low-temperature loops | estimate |
| Air-cooled chiller COP | 2.5 | 3.2 | 4.0 | same | estimate |
| Share of heat to water through chillers | 0.6 | 0.75 | 0.85 | §3 | estimate |
| Cycles of concentration | 3 | 5 | 8 | Lansing EA implies ~3 (§8); SK Bartow permit targets 800 ppm TDS with "8 repeated pass-throughs" (p. 4) | projection, permit |
| Anode slurry water (L/kWh, consumed) | 1.0 | 1.5 | 2.0 | UKBIC slurry solids 42% | estimate |
| Water shipped off site with NMP or trucked (L/kWh, consumed) | 0 | 0.5 | 1.0 | BlueOval City Table 6; StarPlus Table 4 | projection, estimate |
| Other purified water (L/kWh, returned) | 0.2 | 0.5 | 1.0 | — | estimate |
| RO recovery | 0.65 | 0.75 | 0.80 | — | estimate |
| Boiler make-up (L/kWh) | 0.2 | 0.7 | 2.0 | — | estimate |
| Staff per GWh/yr | 25 | 45 | 65 | Six EAs | projection |
| Utilization, sampled | 0.4 | 0.65 | 1.0 | Korean company reports 2022-2025 | reported |

Drift and the evaporative ratio stay shared with the data center model, as 0009 says.

## 10. Gaps

1. **No measured split of a battery plant's heat between cooling water, exhaust and flue.** The share to water (§3)
   is the parameter that matters most after energy intensity, and it rests on a step-by-step estimate and one EA.
   A plant's air permit application (dryer exhaust flows and temperatures, RTO or condenser duty) or a utility's
   large-load filing would narrow it. Michigan EGLE's permit to install for Ultium Lansing (2022) and for LGES Holland
   are the first to request.
2. **No battery plant's outdoor-air flow or measured dry-room load.** The full text of Ahmed, Nelson, Dees (2016) and
   Ahmed et al. (2016, J. Power Sources 322:169-178, NMP drying at about 10 kWh per kg of NMP) would give the
   Argonne model's air flows and condenser duty; neither was read. Vendor design guides (Munters, Bry-Air) and the
   ASHRAE Handbook chapter on desiccant dehumidification were not available.
3. **Electricity of a U.S. EA plant.** The Lansing derivation depends on an unstated grid factor; the BlueOval SK
   figure is a firm contract demand, not use; Panasonic's is a news report. The Ultium Lordstown (Ohio PUCO), StarPlus
   (Indiana IURC) and Ford Marshall (Michigan PSC, Consumers Energy) dockets may hold load forecasts.
4. **Cycles of concentration at Lansing.** The EA implies about 3. Lansing BWL's water quality and any Ultium or LGES
   discharge permit with blowdown flow would settle whether that is the water or a margin.
5. **Process water streams** rest on slurry recipes and two EA waste tables. No source gives a plant's purified water
   demand or RO reject. The Ultium Lansing industrial pretreatment permit (Delta Township or Lansing) would.
6. **Kallitsis meta-analysis and Kurland's full text** were read only through citations. The Northvolt Ett EIA figure
   (400 GWh/yr for 8 GWh/yr) is UNVERIFIED.
7. **Code minimum chiller efficiencies** were not checked against ASHRAE 90.1 in this session.
8. **Seasonality of the share to water.** In winter some process heat preheats make-up air and some leaves in exhaust,
   so the share to water is probably lower in winter than summer. The model holds it steady (0009). Dai's dry-room
   electricity swing (7-26 MJ/kWh) is the only published signal and cannot be split.
9. **Correction to `battery-plant-water.md`, row C10.** Kuki et al. Table 1 maps the water figures as **CATL Debrecen
   27.9 L/kWh, Samsung SDI Göd 55.7, SK Iváncsa 67.0**, not Göd 27.9 and CATL 55.7. Their bases differ: CATL's is an
   estimated 3,378 m³/day (330 days); Göd's is reported 2022 withdrawal (1,458,927 m³) divided by capacity, not output;
   Iváncsa's is the permit's 5,200-6,982 m³/day total including staff use. So Göd's 55.7 is withdrawal and, since 2022
   output was likely below capacity, understates per-kWh use. That note should be updated.

## Sources

Read in this session (primary):

- Kuki, Lakatos, Nagy, Nagy, Kéki (2025), "Energy Use and Environmental Impact of Three Lithium-Ion Battery Factories
  with a Total Annual Capacity of 100 GWh", *Environments* 12(1):24, doi:10.3390/environments12010024. Full text from
  the University of Debrecen repository:
  https://dea.lib.unideb.hu/server/api/core/bitstreams/e2dfdc6e-6c32-418e-a083-9ab5fc8d008c/content
- Degen, Winter, von Dollen, Krause, Wang, Leisewitz (2023), "Energy consumption of current and future production of
  lithium-ion and post lithium-ion battery cells", *Nature Energy* 8:1284-1295, doi:10.1038/s41560-023-01355-z.
  Article, Supplementary Information (Supp. Table 1) and Source Data Figs. 2 and 3:
  https://www.nature.com/articles/s41560-023-01355-z
- Dai, Kelly, Gaines, Wang (2019), "Life Cycle Analysis of Lithium-Ion Batteries for Automotive Applications",
  *Batteries* 5(2):48, §3.2.2: https://mdpi-res.com/d_attachment/batteries/batteries-05-00048/article_deploy/batteries-05-00048.pdf
- UK Battery Industrialisation Centre (Nov 16, 2022), "Pathways to Reduce Energy Consumption in Lithium-Ion Battery
  Cell Manufacturing: A UKBIC Case Study": https://irp.cdn-website.com/2aa2a1de/files/uploaded/WHITE%20PAPER%20(16%20NOV%2022).pdf
- DOE/EA-2189-S1 (Ultium Lansing, Nov 2022), DOE/EA-2189 (Ultium Lordstown and Spring Hill, Aug 2022), DOE/EA-2201
  (BlueOval SK, Mar 2023), DOE/EA-2263 (StarPlus Kokomo, Sept 2024), DOE/EA-2222 (KORE, Sept 2023), DOE/EA-1690
  (A123, Apr 2010): URLs in `battery-plant-water.md`.
- Georgia EPD, SIP application review, SK Battery America, App. 28655 (Dec 22, 2022):
  https://epd.georgia.gov/document/document/28655-narrative/download
- Kentucky PSC Case 2023-00123, KU application for the BlueOval SK special contract (Apr 14, 2023), ¶16:
  https://psc.ky.gov/pscecf/2023-00123/mike.hornung@lge-ku.com/04142023102139/03_-_KU-BOSK_Special_Contract_-_Application.pdf
- Korea Times (Aug 15, 2025), "Major battery makers see steady drop in plant operation rates amid EV market slump":
  https://www.koreatimes.co.kr/amp/business/20250815/major-battery-makers-see-steady-drop-in-plant-operation-rates-amid-ev-market-slump
- Munters (sponsored, Charged EVs, Nov 3, 2021), dry room dehumidification:
  https://chargedevs.com/sponsored/how-to-choose-the-right-dry-room-dehumidification-solution-for-lithium-ion-battery-production/
- Hoge, Bry-Air (Volta Foundation, Oct 1, 2024), "The 'Not-So-Dry' Topic of Battery Dry Rooms":
  https://volta.foundation/the-not-so-dry-topic-of-battery-dry-rooms/
- SSOE, battery manufacturing brochure (qualitative: make-up air handling and humidity control by area):
  https://www.ssoe.com/wp-content/uploads/ssoe_battery-manufacturing-process-mech-brochure.pdf

Abstracts or secondary only (UNVERIFIED unless noted):

- Ahmed, Nelson, Dees (2016), "Study of a dry room in a battery manufacturing plant using a process model",
  *J. Power Sources* 326:490-497, doi:10.1016/j.jpowsour.2016.06.107 (abstract via OSTI 1332969: 16,000 m³, ~400 kW).
- Ahmed, Nelson, Susarla, Dees (2016), "Energy impact of cathode drying and solvent recovery during lithium-ion battery
  manufacturing", *J. Power Sources* 322:169-178, doi:10.1016/j.jpowsour.2016.04.102 (abstract: ~10 kWh per kg NMP).
- Kurland (2020), "Energy use for GWh-scale lithium-ion battery production", *Environ. Res. Commun.* 2:012001,
  doi:10.1088/2515-7620/ab5e1e (abstract: 50-65 kWh electricity per kWh).
- Kansas City Star via Yahoo (2023), Evergy testimony on Panasonic De Soto, 200-250 MW:
  https://www.yahoo.com/news/panasonic-plant-require-much-power-103000534.html
- SMM analysis of Korean battery makers' 2025 utilization:
  https://news.metal.com/newscontent/103835263
- Tribune Chronicle (Oct 2025), GM layoffs at Ultium Cells:
  https://www.tribtoday.com/news/latest-news/2025/10/gm-lays-off-500-workers-at-ultium-cells-amid-slower-ev-demand
- Yuan, Deng, Li, Yang (2017), *CIRP Annals* 66(1):53-56: pilot-scale pack (58.7 GJ of cell production for one pack);
  step shares not checked and not used.
