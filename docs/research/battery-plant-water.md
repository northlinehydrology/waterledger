# Water use at lithium-ion battery plants: evidence for a public-data model

Research note, Nov 9, 2026. Evidence base for a battery plant water model in the waterledger packages, written as
water = f(plant type, capacity, chemistry, cooling design, weather). Public sources only. No code.

Conventions:

- **Withdrawal**: water delivered to the plant (utility supply or wells). **Discharge**: water returned to a sewer,
  a surface water or the ground. **Consumption**: withdrawal minus discharge (evaporation, product, water shipped
  off site). Where a source does not say which it means, the table says "unclear".
- **Status**: *projection* (applicant or agency estimate before operation), *permit* (a limit or authorized volume),
  *reported* (a company's measured annual total), *model* (a process or life-cycle model).
- **Normalized intensity**: gallons per day of withdrawal per GWh/yr of nameplate capacity (gpd per GWh/yr). For
  materials plants, per GWh/yr of cell capacity the material would supply ("GWh-eq"), which needs an assumed material
  loading per kWh, marked **[A]**.
- Conversion: 1 L/kWh = 1,000 m³ per GWh/yr = 2.740 m³/d = **723.8 gpd per GWh/yr**.
  1 acre-foot = 325,851 gal = 1,233.5 m³.
- Page numbers are the printed page numbers of the document unless marked "PDF p.".
- **UNVERIFIED** marks a figure taken from a secondary source or search result that I could not check against the
  primary document in this session.

## 1. Figures

### 1a. Cell manufacturing (gigafactories)

| # | Plant | Capacity | Chemistry | Withdrawal | Discharge | Consumption (derived) | Cooling design stated | Source | Status | gpd per GWh/yr (withdrawal) |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 | Ultium Cells, Delta Twp (Lansing), MI | 103 million cells/yr (EA p. 9). EA implies 350,000 vehicles × 125 kWh = 43.75 GWh/yr (p. 31). GM's stated 50 GWh/yr is UNVERIFIED here | Not stated in EA (pouch, NMP cathode slurry) | 1.5–1.7 MGD, Delta Twp water bought wholesale from Lansing BWL (Saginaw Fm. wells) | 0.56 MGD to sanitary sewer | 0.94–1.14 MGD (63–67%) | Not described | DOE/EA-2189-S1, Supplemental EA, Nov 2022, §3.4 Water Resources, p. 19 | projection | 1.5–1.7e6 / 43.75 = **34,300–38,900** (30,000–34,000 at 50 GWh) |
| C2 | Ultium Cells, Spring Hill, TN | Not stated in EA. GM figure (35 GWh initial, ~50 GWh after expansion) UNVERIFIED | Not stated | 1.4 MGD average; operational peak 1,284 gpm (1.85 MGD); Columbia Power & Water (Duck River) | Not stated | Not stated | Cooling tower make-up is "the most water intensive process"; recirculating system on make-up; options listed for AHU/dehumidifier condensate, roof stormwater, plume capture, blowdown and RO-concentrate reuse (not in base design) | DOE/EA-2189, Aug 2022, §3.3.2, p. 14 | projection | 1.4e6 / 50 = **28,000** (40,000 at 35 GWh). Peak/average = 1.85/1.4 = 1.32 |
| C3 | BlueOval SK, Stanton, TN (BlueOval City) | 45 GWh/yr (EA §1.2) | NMC, Ni ≥ 80%, pouch | 1.2 MGD potable, Megasite Authority wells | 0.33 MGD to Megasite WWTP (Mississippi R.) | 0.87 MGD (72.5%) | Not described | DOE/EA-2201, Mar 2023, §3.2.3.1, p. 22 | projection | 1.2e6 / 45 = **26,700** |
| C4 | BlueOval SK, Glendale, KY (two plants) | 82 GWh/yr (45 + 37) | NMC, Ni ≥ 80%, pouch | 2.4 MGD potable, Hardin Co. Water District No. 2 | 0.66 MGD to Hardin Co. municipal WWTP | 1.74 MGD (72.5%) | Not described | DOE/EA-2201, §3.3.1.1, p. 36 | projection | 2.4e6 / 82 = **29,300** |
| C5 | StarPlus Energy (Stellantis–Samsung SDI), Kokomo, IN | ~67 GWh/yr, two plants | NCA (EA §2) | Maximum ~3,300 gpm "or approximately 2.59 MGD", Indiana American Water. The two numbers disagree: 3,300 gpm = 4.75 MGD; 2.59 MGD = 1,800 gpm | Industrial wastewater 24,000 gpd, stored and trucked off site; sanitary to City of Kokomo (volume not given) | Not derivable | Not described | DOE/EA-2263, Sept 2024, §2.2.4 p. 10 (wastewater); §3.1.3.1 p. 12 (supply) | projection (maximum) | 2.59e6 / 67 = **38,700** (70,900 if 3,300 gpm is right) |
| C6 | SK On–Hyundai, Cartersville (Bartow Co.), GA | 35 GWh/yr (UNVERIFIED, company announcement) | Not stated | 3.6 MGD (UNVERIFIED: Bisnow, Mar 1, 2023, quoting SK's Development of Regional Impact application) | ~1.0 MGD sewage (same, UNVERIFIED) | ~2.6 MGD (~72%) | Seven cooling towers (CT01–CT07), total circulating rate 310,100 gpm (verified: GA EPD air permit narrative, App. 28655, Dec 22, 2022, "Water Cooling Towers") | DRI via Bisnow; GA EPD narrative | projection | 3.6e6 / 35 = **102,900**. Tower circulation: 310,100 / 35 = 8,860 gpm per GWh/yr |
| C7 | KORE Power KOREPlex, Buckeye, AZ (cancelled 2024) | 12 GWh/yr full; Phase 1 6 GWh/yr | NMC pouch and/or LFP prismatic | ~500 acre-ft/yr (≈446,000 gpd), City of Buckeye (groundwater). Not stated whether for Phase 1 or full build | Not stated | Not stated | "closed-loop chiller water"; chiller yard; city water to RO/DI for ultrapure process water | DOE/EA-2222, Sept 2023, §2.1.3, p. 8 | projection | 446,000 / 12 = **37,200** (74,400 if Phase 1 only) |
| C8 | LG Energy Solution, Queen Creek, AZ | Basis of the projection unclear (2022 plan was 11 GWh cylindrical; later enlarged). UNVERIFIED | Cylindrical (2022 plan) | >645 million gal/yr (1.77 MGD) at build-out (UNVERIFIED: Arizona Republic, Oct 7, 2023, quoting a 2022 preliminary rate letter; the town says those build-out numbers are "no longer accurate") | ~328 million gal/yr (0.90 MGD) wastewater (same) | 0.87 MGD (49%) | Not stated | Arizona Republic via Yahoo News | projection, superseded | Not normalized: capacity basis unknown |
| C9 | A123 Systems, Livonia and Romulus/Brownstown, MI (2010) | 2,871 MWh/yr (Romulus + Brownstown at Phase III) + 257 MWh/yr (Livonia) = 3.13 GWh/yr | LFP; vertically integrated: LFP powder synthesis, coating, cells, packs | ~250,000 gpd potable, DWSD (Great Lakes) | 247,098 gpd (Table 2-5): thermal (ammonia) scrubber 133,056; sanitary 77,896; boiler blowdown 15,726; NMP scrubber 11,232; non-contact cooling tower blowdown 6,155; process 3,034 | ~3,000 gpd (≈1%) as stated, which implies almost no evaporative cooling | Small cooling tower blowdown | DOE/EA-1690, Apr 2010, Table 2-5 p. 31; §2.1.11 p. 34; §4.6.1 p. 100 | projection | 250,000 / 3.13 = **79,900** (includes LFP powder plant) |
| C10 | Three Hungarian gigafactories (Samsung SDI Göd; SK On Iváncsa; CATL Debrecen), total ~100 GWh/yr | — | NMC (Kuki et al.) | 28, 56 and 67 L/kWh "water consumption", gate-to-gate (Kuki Table 1): CATL Debrecen 27.9 (an estimated 3,378 m³/day over 330 days), Samsung SDI Göd 55.7 (2022 reported withdrawal, 1,458,927 m³, over capacity rather than output), SK Iváncsa 67.0 (the permit's 5,200-6,982 m³/day, staff included). Corrected Nov 9 from the full text; see `battery-cell-parameters.md` | — | Göd's is withdrawal; the others are estimates or permit totals, not split | — | Kuki, Lakatos, Nagy, Nagy, Kéki (2025), *Environments* 12(1):24, doi:10.3390/environments12010024 | estimate from permit documents | 723.8 × 28 / 56 / 67 = **20,300 / 40,500 / 48,500** |
| C11 | CATL, company-wide, 2025 | Battery system output ≈ 748 GWh (derived: 32,075,665 m³ ÷ 42.88 m³/MWh) | LFP and NMC | 49,244,155 m³ total withdrawal | — | 32,075,665 m³ (65%); intensity 42.88 m³/MWh (= L/kWh) | Water-saving measures named: reclaimed water, steam condensate recovery, RO concentrate reuse, circulating-water desalination | CATL 2025 ESG Report (HKEX filing, Mar 2026), pp. 146–148 and data table pp. 204–205 | reported | Withdrawal 49,244,155 / 748,033 MWh = 65.8 L/kWh → 723.8 × 65.8 = **47,600**; consumption **31,000** |
| C12 | LG Energy Solution, consolidated, 2024 | Production not disclosed | — | 10,922,896 m³ intake (all third-party supply) | Sewage 1,391,848 + wastewater 1,234,049 m³ | 8,297,000 m³ (76%) | Descaling chillers named as a water saving; condensate reuse | LGES ESG Report 2024, data table p. 153 | reported | Not normalized |
| C13 | Argonne GREET battery LCA | — | NMC | "8.6 gal/kWh" water consumption for LIB manufacturing (UNVERIFIED: search snippet of a GREET update document filed in NHTSA-2022-0075; scope, cell-only or cradle-to-gate, not checked). GREET counts only evaporated, reacted or embodied water | — | consumption | — | GREET battery update (Dai et al.); Dai, Kelly, Gaines, Wang (2019) *Batteries* 5(2):48 | model | 8.6e6 / 365 = **23,600** (consumption) |

### 1b. Cathode active material and precursor (pCAM/CAM), and integrated materials plants

| # | Plant | Capacity | Chemistry / process | Withdrawal | Discharge | Consumption | Cooling | Source | Status | Normalized |
|---|---|---|---|---|---|---|---|---|---|---|
| M1 | Ascend Elements Apex 1, Hopkinsville, KY | "enough material to supply over 250,000 EVs annually"; no tonnage in EA | Recycled black mass → hydrometallurgy → metal sulfates, pCAM (and CAM in the 2023 scope); Na2SO4 dryers listed | 310,000 gpd (process + employees), Hopkinsville Water Environment Authority (Lake Barkley) | 150,000 gpd to Hammond-Wood POTW; 80,000 gpd under KPDES KY0113531 (non-contact cooling tower blowdown, RO reject, boiler blowdown) to a tributary of Montgomery Creek | 80,000 gpd evaporated, "primarily" cooling towers (26%) | One cooling tower, 29,166 gpm circulation (air permit in EA appendix) | DOE/EA-2205D (draft), Apr 2023, §3.2.11.2.3.2 p. 35, §3.2.11.2.4.2 p. 36 | projection | [A] 75 kWh/EV → 18.75 GWh-eq: 310,000 / 18.75 = **16,500 per GWh-eq** |
| M2 | Gotion, Green Charter Twp, Mecosta Co., MI (abandoned 2025) | Full: 150,000 t/yr cathode material (two plants) + 50,000 t/yr anode (two plants) (MSF memo Oct 5, 2022; Governor's release Oct 5, 2022). Phase 1 = "Cathode 1/Anode 1/Electrolyte 1" | LFP cathode and anode materials ("This facility will construct anode and cathode materials for LFP batteries") | Phase 1: 715,000 gpd, "the start-up amount", to be reduced when on-site pretreatment operates | Sanitary sewer: 65,000 gpd Phase 1, 130,000 gpd Phase 2; possible NPDES non-contact cooling discharge (not quantified) | Up to ~650,000 gpd (91%) if sewer is the only outflow | "Large scale dehumidification equipment"; water used for cooling, pretreated wastewater recycled to cooling | Green Charter Township, Responses to Public Questions (Apr 2023), answers 1, 4, 6, 19 (pp. 3–4, 7) | projection | [A] Phase 1 = half: 75,000 t CAM + 25,000 t anode. 715,000 gal × 3.785 L = 2,706 m³/d = 987,800 m³/yr → **9.9 m³/t** of all product (13.2 m³/t of CAM alone). [A] 2.2 kg LFP CAM/kWh → 34 GWh-eq → **21,000 per GWh-eq** |
| M3 | Redwood Materials, McCarran (TRIC), NV | Build-out: >100,000 t/yr CAM, >35,000 t/yr copper foil, hydromet lines >2,500 and >10,000 t/yr | Recycling (hydromet) + pCAM/CAM + Cu foil | Up to 550 acre-ft/yr at full build-out (TRI-GID agreement) = 491,000 gpd = 678,400 m³/yr; reclaimed water as process water from 2023 | Target: zero process-water discharge; ~90% of water not evaporated is recycled on site | Most of withdrawal, by design | Not described | DOE/EA-2228, Nov 2023, §2.2.4 (PDF footer p. 2-10); phases p. 2-5 | permit/agreement (maximum) | 678,400 m³ / 100,000 t = **6.8 m³/t CAM** (upper bound; includes foil and hydromet). [A] 1.4 kg high-Ni CAM/kWh → 71 GWh-eq → **6,900 per GWh-eq** |
| M4 | Process model, NMC333 by co-precipitation (Argonne) | 6,500 kg/day plant (~2,370 t/yr) | NMC333, Na2CO3 or NaOH precipitation | 15 L process water per kg NMC | — | — | — | Ahmed, Nelson, Gallagher, Susarla, Dees (2017), *J. Power Sources* 342:733–740, doi:10.1016/j.jpowsour.2016.12.069 (abstract, OSTI 1368567) | model | 15 m³/t. [A] 1.6 kg CAM/kWh → 24 L/kWh → **17,400 per GWh-eq** (process water only, no cooling) |
| M5 | A123 powder blocks (in C9) | 11 powder blocks, 90 t/month each (Table 2-1) | LFP powder | — | Powder sites' thermal scrubber effluent ≈ 24,192 gpd per site, 133,056 gpd total | — | — | DOE/EA-1690, Tables 2-1 and 2-5 | projection | Thermal scrubber alone: 133,056 gal/d × 3.785 / (11 × 90 t/month ÷ 30.4) = **15.5 m³/t** LFP powder |

### 1c. Other plant types (brief)

| # | Plant | Capacity | Withdrawal / discharge | Source | Normalized |
|---|---|---|---|---|---|
| O1 | ENTEK separator, Terre Haute, IN | 1.4 billion m²/yr after Phases 1–2 (~1.4 million EVs); Phase 3 +0.7 billion m² | On-site wells for industrial cooling: 0.62 MGD per phase, 1.23 MGD after Phase 2, 1.85 MGD after Phase 3. "Roughly half" evaporated; ~1 MGD total to Terre Haute sewer. Blowdown 24 gpm (34,600 gpd) per building. (§2.1 on p. 6 says "66 million gallons per day"; that conflicts with §3.3.2 and looks like an error.) | DOE/EA-2266, Sept 2024, §3.3.2, pp. 17–18 | 1.23e6 / 1.4e9 m² = 0.88 gpd per 1,000 m²/yr. [A] 75 kWh/EV → 105 GWh-eq → **11,700 per GWh-eq** |
| O2 | Syrah active anode material (natural graphite), Vidalia, LA | 11,250 t/yr AAM (~128,000 EVs/yr) | ~40,000 gpd wastewater (dilute NaCl/CaCl2) to Town of Vidalia; supply volume not given | DOE/EA-2181, Apr 2022, §3.12, p. 18 | Discharge 4.9 m³/t AAM |
| O3 | Tesla Gigafactory Nevada (cells by Panasonic) | ~35–38 GWh/yr cells (UNVERIFIED) | Up to 2,500 acre-ft/yr (2.2 MGD), early planning estimate attributed to the Nevada State Engineer (UNVERIFIED, secondary). NDEP groundwater discharge permit NS2020502: TRI-GID reclaimed water treated on site for evaporative cooling; tower blowdown and RO reject to a lined trench, dust control and irrigation; 2026 modification adds a battery building (385 Milan Dr.) that uses reclaimed water in slurry preparation and closed-loop cooling. No flows in the fact sheet | NDEP fact sheet NS2020502 (draft 2, major modification July 2026), pp. 1–2 | Not normalized |
| O4 | Panasonic Energy, De Soto, KS | 32 GWh/yr | No plant figure found. City water plant expanded from 2 to 8 MGD, fully funded by Panasonic | WaterWorld, Feb 2, 2026 (B. Morehead, Garney); Spectrum News, Sept 25, 2025 | Infrastructure only |
| O5 | Ford BlueOval Battery Park Michigan, Marshall | 20 GWh/yr LFP (UNVERIFIED) | No plant figure found. Built for the MAJOR campus: high-service pump station 10.5 MGD (four 1,800-gpm pumps); up to 5 MGD from Battle Creek via the Emmett Twp loop; 4.5 MG ground storage tank; sanitary pump station 3.5 MGD initial | City of Marshall fact sheets 1, 5, 7 (choose-marshall) | Infrastructure only; campus-wide |

## 2. Range by plant type

**Cell plants (withdrawal).** DOE environmental assessments for six U.S. cell plants (C1–C5, C7) give
**27,000–39,000 gpd per GWh/yr** (37–54 L/kWh), taking the lower reading where the EA is ambiguous. The
company-reported and permit-based values (C10, C11) agree: 20,300–48,500 gpd per GWh/yr (28–67 L/kWh). Two values
lie outside the range: SK Bartow at ~103,000 (secondary source; it agrees with the tower circulation rate in the air
permit, see §4), and A123 at ~80,000 (a 2010 plant, small, and including LFP powder synthesis). A working central value
is **~30,000 gpd per GWh/yr withdrawal (≈41 L/kWh)**, with an observed range of 20,000–50,000 and a design-peak factor of
about 1.3 (Spring Hill).

**Cell plants (consumption fraction).** Where an EA gives both supply and discharge, 63–73% of withdrawal is consumed
(Lansing 63–67%, BlueOval SK 72.5% at both sites, SK Bartow ~72%). Company reports agree: CATL 65%, LGES 76%. Queen
Creek's superseded 2022 projection (49%) and A123 (~1%) are the exceptions. Consumption is therefore about
**19,000–28,000 gpd per GWh/yr (≈27–38 L/kWh)**, and discharge 7,000–13,000.

**CAM/pCAM and integrated materials plants.** The figures are fewer and harder to compare: 6.8–15.5 m³/t of product,
or ~7,000–21,000 gpd per GWh-eq [A]. They do not support a claim that pCAM plants use an order of magnitude more water
per GWh-eq than cell plants. The figures found are of the same order or lower. Where materials plants differ is in
**discharge quality** (sulfate- and sodium-rich brine from co-precipitation; ammonia scrubber effluent) and in the
**consumption fraction**, which ranges from 26% (Ascend, mostly to sewer) to near 100% (Redwood's zero-discharge
target). Caveats: none of these is a pure NMC pCAM plant with a stated sulfate brine volume; Ascend and Redwood combine
recycling with cathode production; and the GWh-eq conversion depends on the [A] loadings below.

| [A] Loading used to convert material tonnes to GWh-eq | Value | Basis |
|---|---|---|
| NMC111/333 CAM | 1.6 kg/kWh | Order of magnitude from cell-design models (BatPaC class); not checked in this session |
| High-Ni (NMC811/NCA) CAM | 1.4 kg/kWh | same |
| LFP CAM | 2.2 kg/kWh | same |
| Energy per EV pack | 75 kWh | Assumption; the EAs use 70 (StarPlus) and 125 (Ultium) |

**Other.** Separator (ENTEK): ~11,700 gpd per GWh-eq [A], nearly all for equipment cooling, about half evaporated.
Natural-graphite anode (Syrah): discharge ~4.9 m³/t. Synthetic graphite (graphitization), lithium hydroxide refining
and recycling were not covered beyond M1 and M3; see Gaps.

## 3. Drivers

1. **Heat rejection.** In the U.S. cell-plant EAs, the largest single use is cooling-tower make-up (stated directly
   for Spring Hill; implied elsewhere by the 63–73% consumption fraction, which only evaporation can explain at that
   scale). The heat comes from electrode drying ovens, NMP condensation and recovery, dry-room air handling,
   formation and aging (charge and discharge cycling), and compressors. Natural gas boilers or thermal oil heaters
   supply the drying heat (SK Bartow: twelve 30–35 MMBtu/h hot-oil heaters and six 50.7 MMBtu/h boilers).
2. **Plant energy intensity.** Kuki et al. (2025) report 30–35 kWh of energy per kWh of cell capacity (electricity plus
   gas, including offices) at the Hungarian plants. A physical check: if a fraction *f* of that energy leaves through
   evaporative towers, consumption ≈ *f* × 30–35 kWh_th × 1.47 L per kWh_th (latent heat of water ≈ 2.43 MJ/kg at 30 °C).
   For *f* = 0.5–0.75 that gives **22–39 L/kWh**, which brackets the 27–38 L/kWh consumption found in §2. This is my
   derivation and should be treated as an estimate, but it closes: the reported water is about what the energy balance
   requires. It suggests building the cell-plant model like the data center model: heat load from energy intensity ×
   production, rejected through towers or dry coolers, with weather setting the evaporated share.
3. **Cooling design.** Wet towers (most EAs), closed-loop air-cooled chillers (KORE, Arizona), and reclaimed-water
   towers (Tesla Nevada, Redwood) are all in the record. KORE's ~37,000 gpd per GWh/yr with "closed-loop chiller water"
   shows that a chiller description alone does not mean low water; the EA does not say how the chillers reject heat.
4. **Process and ultrapure water.** Plants run RO/DI for process water (KORE, Ascend, Tesla). Anode slurry is
   water-based and the water is evaporated in the dryers. RO reject and boiler blowdown are discharged. NMP recovery
   (condensers and water scrubbers) produces an NMP–water mixture: Lansing reports 161,500 lb/yr of off-spec NMP (EA
   Table 4); BlueOval City reports 144 million lb/yr of "NMP scrap" leaving by tanker for recycling (EA Table 6, p. 34),
   ~46,000 gpd if it were water [A: 8.6 lb/gal; its water fraction is not stated]. Water shipped off site in recovered
   solvent counts as consumption for the watershed.
5. **Sanitary.** Staff water is small but not negligible. A123's sanitary flow was 31% of its discharge (77,896 of
   247,098 gpd). The Ultium EAs give 1,300 (Spring Hill) and 1,522 (Lansing) employees.
6. **Materials plants.** Withdrawal per tonne of product is set by washing and filtration of the precipitate and by
   scrubbing (ammonia or acid off-gas). Consumption is set by cooling and, where it is used, by zero-liquid-discharge
   crystallization (Redwood).
7. **Recycle and reuse.** Projected reuse moves the numbers a lot: Gotion's 715,000 gpd is a "start-up amount" to be
   reduced by pretreatment and reuse; Redwood plans ~90% process-water recycling; BlueOval City returns treated
   wastewater from the Megasite WWTP to the adjacent assembly plant.

## 4. Cooling share, and how weather changes it

- **Share.** No document gives a measured split between cooling and process water. The best evidence on the share:
  - Spring Hill says cooling-tower make-up is the most water-intensive process.
  - Consumption fractions of 63–76% at cell plants imply that evaporation, almost all of it in towers, is at least
    about two-thirds of withdrawal. Blowdown adds to that: at 4–6 cycles of concentration [A], blowdown is 20–33% of
    evaporation.
  - Cooling, evaporation plus blowdown, is therefore an estimated **75–90% of cell-plant withdrawal** [A], with
    process water, RO reject, boiler make-up and sanitary making up the rest.
  - At Ascend (pCAM), evaporation is 26% of withdrawal and towers are a smaller share.
  - At ENTEK (separator), cooling is essentially all of the well water.
- **Tower sizing.** SK Bartow's towers circulate 310,100 gpm for ~35 GWh/yr (8,860 gpm per GWh/yr). With the usual
  evaporation estimate of 0.00085 × range (°F) × circulation, a 10 °F range gives ~2,640 gpm (3.8 MGD) of evaporation at
  full design load. That agrees with the 3.6 MGD in SK's DRI application and suggests the DRI figure is a design-day
  number, not an annual average.
- **Weather.**
  - Spring Hill's EA says condensate from air handlers and dehumidifiers "varies on a seasonal basis", as does plume
    capture.
  - Tesla's Nevada permit describes blowdown from the towers in winter and from the chiller units the rest of the
    year.
  - Dry rooms are held at dew points far below outdoor air, so their make-up air carries a latent load that rises
    with outdoor humidity. Summer humidity therefore raises both chiller load and tower evaporation, the same
    mechanism as data center cooling. This comes from HVAC first principles, not from a source; the EAs give no
    monthly numbers.
  - The only quantified seasonal or peak signal is Spring Hill's peak-to-average ratio of 1.32.
- **Implication for the model.** The waterledger cooling components (hourly heat load → tower evaporation and
  blowdown, or dry cooler) can be reused. What the battery model has to add is the plant heat load: energy intensity
  per kWh of production (with a dry-room term that depends on outdoor humidity) plus a non-cooling base (process,
  RO reject, boiler, sanitary) that does not depend on weather.

## 5. Chemistry

- **Cell plants.** The EAs do not separate water by chemistry, and the cell-plant figures (NMC pouch at BlueOval SK, NCA
  at StarPlus, unstated at Ultium) fall in one band. Both NMC and LFP cathodes are usually coated from NMP slurry, so
  the main water-using steps are the same. Per kWh, LFP's lower specific energy means more electrode area, drying and
  formation per kWh. This plausibly raises energy and water per kWh. Not quantified in any source found. A 2022
  GREET-based regional LCA of NMC batteries of varying nickel content (*Sustainable Materials and Technologies*,
  article S221499372200029X) reports lower water per kWh with higher nickel content. This is supply-chain water, not
  plant water; the authors and figures are UNVERIFIED (search snippet only).
- **Materials plants.**
  - NMC/NCA pCAM by sulfate co-precipitation produces a sodium sulfate stream: Ascend's air permit lists
    Na2SO4 dryers, so its sulfate is crystallized, not discharged.
  - A vendor (NOVONIX white paper) puts pCAM byproduct at 1–3 t per t pCAM (vendor-sourced, not independently checked).
  - LFP CAM (A123, Gotion) has no sulfate co-precipitation step at the CAM plant. A123's largest stream was ammonia
    scrubber effluent from powder calcination (~15.5 m³/t). Iron phosphate precursor, often made upstream, is a wet
    process and was not covered.
  - Gotion's LFP figure (9.9–13.2 m³/t) and Argonne's NMC333 model (15 m³/t) are of similar magnitude.

## 6. Gaps

1. **No measured plant-level water for any U.S. cell plant.** Every U.S. figure is a pre-construction projection. The
   cheapest way to get measured data is probably from public records requests or utility billing reports: Delta
   Township/Lansing BWL (Ultium Lansing, now LGES), Columbia Power & Water (Spring Hill), Warren/Lordstown (Ultium
   Lordstown, which has no water figure in its EA), Holland BPW (LGES Holland), Hardin Co. Water District No. 2
   (Glendale). EGLE Part 327 or large-quantity withdrawal reports would cover only plants with their own wells.
2. **Capacity basis.** The EAs often omit GWh/yr (Spring Hill, Lansing) or are unclear about phases (KORE, Queen
   Creek). Several capacities above are company announcements marked UNVERIFIED.
3. **Michigan.**
   - Figures exist for Ultium Lansing, Gotion (Phase 1 only) and A123 (2010).
   - None found for Ford Marshall (infrastructure only), LGES Holland, Our Next Energy (Van Buren Twp), or Gotion's
     later phases.
4. **Cooling vs. process split** is not measured anywhere public. No monthly or seasonal series was found.
5. **Pure pCAM/CAM plants.** No public U.S. figure for a dedicated NMC pCAM/CAM plant with a stated sulfate brine
   volume. Candidates:
   - Quebec impact studies for Bécancour (EcoPro CAM, Ultium CAM; registre des évaluations environnementales).
   - BASF Harjavalta (Finland) permit decisions.
   - LG Chem Clarksville, TN (TDEC permits).
   - Umicore Loyalist, ON.
6. **Literature not read in full** (access blocked or Cloudflare-gated in this session):
   - the GREET battery update documents;
   - Dai et al. (2019) full text;
   - Kuki et al. (2025) full text (plant mapping and whether "consumption" is withdrawal).
   - The GREET 8.6 gal/kWh value is UNVERIFIED.
7. **Company data.**
   - CATL's 2025 company-wide intensity (withdrawal 65.8 L/kWh, consumption 42.9 L/kWh) may include non-cell
     operations (materials, recycling subsidiaries). Its scope note does not settle this.
   - LGES does not report production, so no intensity can be computed.
   - Panasonic Energy reports consolidated withdrawal per yen of sales. Whether the Nevada plant is inside the
     boundary was not checked (UNVERIFIED).
8. **Other plant types.** Synthetic-graphite anode (graphitization is mostly electric heat), lithium hydroxide refining
   (e.g., Tesla Robstown, TX), electrolyte and LiPF6 plants, and battery recycling beyond Ascend and Redwood were not
   covered. DOE's BIL battery-materials EAs (listed, anonymized, in the BIL Environmental Synopsis appended to the Ascend EA, pp. 11–13) and the Li-Cycle Rochester
   EA (DOE/EA-2219) are the next places to look.
9. **SK Bartow 3.6 MGD** should be checked against the DRI form on Georgia DCA's DRI site before it is used; it is the
   one high outlier and it rests on a news report.

## Sources

Primary documents read in this session:

- DOE/EA-2189-S1, Supplemental EA, Ultium Cells Lansing (Nov 2022):
  https://www.energy.gov/sites/default/files/2022-11/supplemental-ea-fonsi-ea-2189-S1-ultium-cells-battery-2022-11.pdf
- DOE/EA-2189, EA, Ultium Cells Lordstown and Spring Hill (Aug 2022):
  https://www.energy.gov/sites/default/files/2022-08/LPO_Ultium_Lordstown-SpringHill_EA_FONSI_August2022.pdf
- DOE/EA-2201, EA, BlueOval SK Stanton TN and Glendale KY (Mar 2023):
  https://www.energy.gov/sites/default/files/2023-03/2023_03_02_LPO-BlueOvalSK_EAv6.0_signed.pdf
- DOE/EA-2263, Final EA, StarPlus Energy Kokomo (Sept 2024):
  https://www.energy.gov/sites/default/files/2024-09/StarPlusKokomo_FinalEA_Sept2024.pdf
- DOE/EA-2222, Final EA, KORE Power KOREPlex (Sept 2023):
  https://www.energy.gov/sites/default/files/2023-09/KORE_PowerEA_FONSI_Sept2023.pdf
- DOE/EA-1690, Final EA, A123 Systems (Apr 2010):
  https://www.energy.gov/sites/default/files/nepapub/nepa_documents/RedDont/EA-1690-FEA-2010.pdf
- DOE/EA-2205D, Draft EA, Ascend Elements Apex 1 (Apr 2023):
  https://www.netl.doe.gov/sites/default/files/2023-04/Ascend%20Elements%20Apex%201%20Draft%20EA%20Public%20Comment.pdf
- DOE/EA-2228, Final EA, Redwood Materials McCarran (Nov 2023):
  https://www.energy.gov/sites/default/files/2023-11/231128_Final_Redwood_EA_FONSI.pdf
- DOE/EA-2181, EA, Syrah Technologies Vidalia (Apr 2022):
  https://www.energy.gov/sites/default/files/2022-08/LPO_Syrah_EA_FONSI_April%202022_1.pdf
- DOE/EA-2266, Final EA, ENTEK Terre Haute (Sept 2024):
  https://www.energy.gov/sites/default/files/2025-01/final-fonsi-ea-2266-entek-lithium-separator-2024-09.pdf
- Green Charter Township, Gotion Responses to Public Questions (Apr 2023):
  https://greentownship.org/_files/ugd/958d79_b7855ced7af74771b4b6f58050402efc.pdf
- Michigan Strategic Fund memo, Gotion incentives (Oct 5, 2022):
  https://www.greentownship.org/_files/ugd/958d79_1c1c5048c7af4aab90f0445cda3e590d.pdf
- Governor's release, Gotion Big Rapids (Oct 5, 2022):
  https://www.michigan.gov/whitmer/news/press-releases/2022/10/05/whitmer-announces-new-battery-component-manufacturing-facility-in-big-rapids
- Georgia EPD air permit narrative, SK Battery America Cartersville, App. 28655 (Dec 22, 2022):
  https://epd.georgia.gov/document/document/28655-narrative/download
- NDEP fact sheet, Tesla groundwater discharge permit NS2020502 (draft 2):
  https://www.ndep.nv.gov/uploads/documents/FactSheet_PermitNumNS2020502_Draft2.pdf
- CATL 2025 ESG Report (HKEX, Mar 2026):
  https://www1.hkexnews.hk/listedco/listconews/sehk/2026/0309/2026030901390.pdf
- LG Energy Solution ESG Report 2024:
  https://www.lgensol.com/upload/file/sustainability/LG_Energy_Solution-2024_ESG_Report_EN_FFF%5B1%5D.pdf
- City of Marshall infrastructure fact sheets 1, 5 and 7:
  - https://choose-marshall.s3.amazonaws.com/images/Fact-Sheet-1-V6.pdf
  - https://choose-marshall.s3.amazonaws.com/images/Fact-Sheet-5-V6.pdf
  - https://choose-marshall.s3.amazonaws.com/images/Fact-Sheet-7-V9.pdf
- Ahmed et al. (2017), abstract: https://www.osti.gov/biblio/1368567
- Kuki et al. (2025), abstract (via Semantic Scholar): https://doi.org/10.3390/environments12010024

Secondary sources (figures marked UNVERIFIED unless noted):

- Bisnow, Mar 1, 2023, SK Bartow DRI application (3.6 MGD, 1 MGD sewage):
  https://www.bisnow.com/atlanta/news/economic-development/sk-battery-plant-in-bartow-expected-to-churn-40b-economic-impact-117886
- Arizona Republic via Yahoo, Oct 7, 2023, LGES Queen Creek (645 and 328 million gal/yr):
  https://www.yahoo.com/news/updates-queen-creek-lg-battery-130113521.html
- WaterWorld, Feb 2, 2026, De Soto water plant expansion for Panasonic. Article text verified; it gives no plant
  figure:
  https://www.waterworld.com/water-utility-management/article/55354582/collaborative-delivery-drives-fast-track-water-treatment-expansion-for-panasonic-energy-in-kansas
- Dai, Kelly, Gaines, Wang (2019), *Batteries* 5(2):48: https://www.mdpi.com/2313-0105/5/2/48 (abstract only)
- Kelly, Dai, Wang (2019), *Mitig. Adapt. Strateg. Glob. Change*, doi:10.1007/s11027-019-09869-2 (abstract only)
