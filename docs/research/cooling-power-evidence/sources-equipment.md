# Dry vs evaporative cooling: electricity cost, peak, and grid water intensity — source log

Compiled 2026-11-16 for the Water Ledger methods review. Downloads and extracted text are in
`/private/tmp/claude-501/-Users-andrew-northline--claude-worktrees-silly-hodgkin-473649/33b7e5e1-2a0f-4a84-a5ed-1982542ff33b/scratchpad/dl-equipment/`.

Conventions
- "Read" = I read the primary document text (pdftotext). "Page via WebFetch" = read through a fetch tool's summary of the page (moderately reliable, numbers checked where possible). "Snippet, unverified" = search-engine summary only.
- Quotes are short and exact. Quotes are limited to U.S. government documents (NREL, PNNL, LBNL, ASHRAE-addendum table values are facts). Copyrighted sources are paraphrased, marked "(paraphrase)".
- "My arithmetic" marks conversions or cross-checks I computed; they are not source numbers.
- Unit conversions used: COP = 3.517 / (kW/ton); COP = EER / 3.412.

---

## Model figures being checked (from the brief)

Per 100 MW IT, hourly on ERA5, shared ~23 C facility water loop:
- Year PUE dry vs towers: 1.175 vs 1.137 (Grand Rapids), 1.192 vs 1.150 (Loudoun), 1.233 vs 1.176 (Dallas). Differences 0.038 / 0.042 / 0.057 (3.3–4.8% of total facility energy).
- Hottest hour: 134–138 MW dry vs 127 MW towers (+5.5–8.7% total; +26–41% of the non-IT overhead, my arithmetic).
- Dallas chilled-water plant (7–13 C): 1.351 / 149 MW dry vs 1.268 / 134 MW towers.
- Towers ~0.54 MGD per 100 MW in Loudoun (= 0.85 L per IT kWh, my arithmetic).
- Air-cooled chiller curves from ASHRAE 90.1 PRM (PNNL-26917).

---

## 1. Chiller efficiency (standards, lab curves, maker data)

### 1.1 ASHRAE 90.1-2019 Addendum x — Table 6.8.1-3 (chilling packages)
- Citation: ANSI/ASHRAE/IES Addendum x to Standard 90.1-2019. Approved Dec 9, 2021 (file dated 2022-02-04).
- URL: https://www.ashrae.org/file%20library/technical%20resources/standards%20and%20guidelines/standards%20addenda/90_1_2019_x_20220204.pdf
- Type: standard (official addendum text). Read.
- Numbers (Path A / Path B; AHRI 550/590 rated: air-cooled at 95 F ambient, water-cooled at 85 F entering condenser water, 44 F leaving chilled water):
  - Air-cooled, all sizes: FL EER ≥ 10.100 (Path A) / ≥ 9.700 (Path B). IPLV.IP ≥ 13.700 (<150 t), ≥ 14.000 (≥150 t) Path A; ≥ 15.800 / ≥ 16.100 Path B.
    - COP (my arithmetic): FL 2.96 (A), 2.84 (B); IPLV 4.02–4.10 (A), 4.63–4.72 (B). Air-cooled EER includes condenser-fan power.
  - Water-cooled centrifugal ≥ 600 t (also 400–600 t): FL ≤ 0.5600 kW/ton, IPLV ≤ 0.5000 (A); FL ≤ 0.5850, IPLV ≤ 0.3800 (B).
    - COP: FL 6.28 (A) / 6.01 (B); IPLV 7.03 (A) / 9.26 (B). Excludes tower fans and condenser pumps.
  - Water-cooled positive displacement (screw) ≥ 600 t: FL ≤ 0.5600, IPLV ≤ 0.5000 (A); FL ≤ 0.5850, IPLV ≤ 0.3800 (B). 300–600 t: FL ≤ 0.6100 / IPLV ≤ 0.5200 (A).
- Quote (table footnote b, p.3): "Both the full-load and IPLV.IP requirements must be met or exceeded".
- Note: The full-load COP of a code-minimum air-cooled chiller (2.96, incl. fans) is about 47% of a large water-cooled centrifugal (6.28, excl. tower and pumps). Once you add tower fans (~0.013 kW/kW heat, below) and condenser pumping, the plant-level ratio is closer to 0.5–0.55. Annual and peak: matters only for the chilled-water (7–13 C) case. It does not apply to the 23 C dry-cooler case, where no compressor runs most hours.
- Search-side caveat (snippet, unverified): the FEMP "minimum efficiency tables" page lists some different centrifugal values (e.g., 0.544 FL for 150–300 t). I did not reconcile this. The addendum text above is the primary source.

### 1.2 PNNL-26917 — ASHRAE 90.1-2016 Performance Rating Method Reference Manual (chiller curves)
- Citation: Goel S, Rosenberg M, Eley C. *ANSI/ASHRAE/IES Standard 90.1-2016 Performance Rating Method Reference Manual*. PNNL-26917, Pacific Northwest National Laboratory, September 2017. Curves sourced to COMNET 2017.
- URL: https://www.pnnl.gov/main/publications/external/technical_reports/PNNL-26917.pdf
- Type: government lab. Read (pp. 3.225–3.228, Tables 77–83, Eq. 54–57).
- Form: Poperating = Prated × EIR_FPLR × EIR_FT × CAP_FT (Eq. 57). Air-cooled curves use chilled-water supply temp and outdoor dry bulb. Valid Tchws 40–54 F, Todb 40–115 F (Table 77/80). Note (p.3.225): "Separate curves are provided for Path A and Path B chillers in COMNET".
- Air-cooled screw, my evaluation of Tables 77/80 (at full available load, efficiency penalty = EIR_FT):

  | Tchws | Todb | CAP_FT | EIR_FT (kW/kW ÷ rated) | COP if rated 2.96 |
  |---|---|---|---|---|
  | 44 F | 75 F | 1.110 | 0.770 | 3.84 |
  | 44 F | 95 F | 1.003 | 1.000 | 2.96 |
  | 44 F | 105 F | 0.945 | 1.154 | 2.57 |
  | 44 F | 110 F | 0.915 | 1.241 | 2.39 |
  | 44 F | 115 F | 0.885 | 1.334 | 2.22 |
  | 54 F | 95 F | 1.149 | 0.894 | 3.31 |
  | 54 F | 115 F | 1.000 | 1.191 | 2.49 |

  Air-cooled scroll is similar: at 44 F/115 F, CAP 0.878 and EIR 1.376.
- Water-cooled centrifugal (Tables 78/81), 44 F CHWS: EIR_FT 0.690 at 60 F condenser water, 0.861 at 75 F, 0.995 at 85 F. CAP_FT is about 0.95–1.03 over that range.
- Note: From 95 F to 115 F, a code air-cooled chiller loses about 11–12% of capacity, and its kW per kW of cooling rises about 33%. A tower plant's condenser water moves with wet bulb, which spans much less than dry bulb, so its penalty on the design day is far smaller. This supports a hot-hour gap that is larger than the annual gap. The curves end at 115 F, so Dallas or Phoenix extremes above that are extrapolation.
- Cross-check of the model's Dallas chilled-water peak (my arithmetic, code-minimum equipment, ~100 MW of heat):
  - Air-cooled at ~110 F: about 0.338 × 1.24 = 0.42 kW/kW, or about 42 MW of chiller power.
  - Water-cooled centrifugal at 0.56 kW/ton (0.159 kW/kW): about 16 MW, plus about 1.3–1.6 MW of tower fans and about 1–2 MW of condenser pumping, for about 19 MW.
  - The gap is about 20–25 MW per 100 MW. The model's 15 MW gap (149 vs 134) is smaller. Possible reasons: chillers better than code minimum, a lower ambient in the model's hottest hour, or 7–13 C chilled water (above the 44 F rating point, which helps both plants). Worth checking which rated COP the model applies.

### 1.3 Trane product pages and catalogs on high ambient (snippet, unverified)
- Trane Series R / RTAC catalogs (scribd, manualsonline copies): the standard ambient range is 25–115 F, a high-ambient option goes to 125 F, and above 115 F a design "can result in excessive head pressures" (Trane catalog, snippet). The Trane Sintesis page lists an operating envelope of -4 to 130 F.
- URLs: https://www.trane.com/commercial/north-america/us/en/products-systems/chillers/air-cooled-chillers/sintesis.html ; https://elibrary.tranetechnologies.com/public/commercial-hvac/Literature/Product%20Catalog/RLC-PRC049K-EN_04022022.pdf (not read).
- Type: maker catalog. No published %-capacity derate at 115 F was found. Makers point users to their selection software (TOPSS, Carrier eCat). Gap: no maker table read.

### 1.4 Free-cooling air-cooled chillers, annual efficiency
- Vertiv white paper (see 3.4): an air-cooled chiller with free-cooling economization, 3 MW, Ashburn VA, pPUE 1.13 with WUE 0. Read.
- 7x24 Exchange magazine, Spring 2015: free-cooling chillers reach annual mechanical PUE < 1.2, as low as 1.08. Snippet, unverified. URL: https://7x24exchange.org/spring15_/7x24Spring2015Magazinefx/files2fx/assets/basic-html/page-40.html
- Trane India case study: free-cooling air-cooled chiller, "up to 18%" annual energy savings. Vendor, snippet, unverified. URL: https://www.trane.com/commercial/asia-pacific/in/en/about-us/case-studies/data-center/pioneering-a-new-standard--delivering-india-s-first-free-cooling.html

---

## 2. Heat-rejection equipment: fan power, approach, pump head

### 2.1 ASHRAE 90.1 Table 6.8.1-7 heat-rejection minimums (as reproduced by BAC)
- Citation: Baltimore Aircoil Co., "Technical Resources: Codes and Standards" (J22), 2015, reproducing ASHRAE 90.1-2013 Table 6.8.1-7.
- URL: https://baltimoreaircoil.com/es/download_api_endpoint/1187/j22_tr_codesstandards_20150914.pdf
- Type: maker document reproducing a standard. Read.
- Numbers:
  - Axial-fan open cooling tower: ≥ 40.2 gpm/hp at 95 F in / 85 F out / 75 F wb (10 F range, 10 F approach).
  - Axial closed-circuit tower: ≥ 14.0 gpm/hp at 102/90/75.
  - Air-cooled condenser: ≥ 176,000 Btu/h·hp at 125 F condensing and 95 F entering dry bulb.
- My arithmetic, nameplate fan kW per kW of heat:
  - Open tower: 0.0127 (≈ 0.056 kW/ton of chiller at 3 gpm/ton; a CEC filing cites CTI at ≤ 0.056 kW/ton, snippet).
  - Closed-circuit tower: about 0.030 (incl. spray pump).
  - Air-cooled condenser: 0.0145.
- Note: At their rating points, open towers and dry coils have similar fan power per kW of heat. The difference is the sink temperature (wet bulb vs dry bulb), not fan energy. In a dry-cooler design, the energy cost shows up as a warmer loop or more compressor hours, not as fan power.

### 2.2 Kaltra Mistral-W dry cooler selection guide (maker catalog)
- Citation: Kaltra, *Mistral-W High-performance dry coolers*, Selection Guide Ver. 2.0 (c. 2020).
- URL: https://kaltra.com/wp-content/uploads/2020/11/SG_Mistral-W_Ver.2.0_EN.pdf
- Type: maker catalog. Read (W80 performance tables).
- Rating: Tair 25 C, fluid in 40 C, out 35 C, 35% ethylene glycol, so a 10 K approach (leaving fluid minus air).
- Numbers:
  - 6-pole fans: 268.1 kW with 6.88 kW of fans (0.026 kW/kW); 1,268.3 kW with 27.52 kW (0.022).
  - 8-pole (slower) fans: 180.5 kW with 3.08 kW (0.017); 972.2 kW with 12.32 kW (0.013).
  - Fluid pressure drop 11–102 kPa per unit (catalog column).
- Note: Dry-cooler fan power runs about 1.3–2.6% of heat rejected at a 10 K approach. It falls roughly with the cube of fan speed at part load. A 23 C loop at a 10 K approach needs air at or below about 13 C before the dry cooler can carry full load without a compressor.

### 2.3 Chart Industries, *Kaldris data center cooling* (maker brochure)
- URL: https://files.chartindustries.com/Kaldris_datacenter_cooling.pdf
- Type: maker. Read.
- Content: large 24–28 ft fans with velocity-recovery stacks for air-cooled heat exchangers. Their example compares a 372-fan layout to 24–36 large fans at the same 372 total fan BHP, and notes that fan power scales with speed cubed (paraphrase).
- Note: Supports fan power as a small, strongly part-load-sensitive term. No kW/kW figure given.

### 2.4 NREL thermosyphon notes on dry-cooler pressure drop
- See 3.1. The NREL report says dry coolers' water-side pressure drop is "typically much higher" than the TSC's single-pass bundle (p.8).
- Gap: I found no numeric pump-head comparison between a glycol dry-cooler loop and a tower condenser loop. Glycol also lowers heat-transfer efficiency (NREL, p.9, qualitative).

---

## 3. Studies with measured or modeled energy and water

### 3.1 NREL TP-2C00-72196 (2018) — thermosyphon hybrid, 24 months measured
- Citation: Sickinger D, Van Geet O, Belmont S, Carter T, Martinez D. *Thermosyphon Cooler Hybrid System for Water Savings in an Energy-Efficient HPC Data Center: Results from 24 Months and Impact on WUE*. NREL/TP-2C00-72196, Sept 2018. OSTI 1471661.
- URL: https://www.nrel.gov/docs/fy18osti/72196.pdf (nrel.gov no longer resolves; obtained from https://docs.nlr.gov/docs/fy18osti/72196.pdf)
- Type: government lab, measured. Read.
- Numbers:
  - IT load averaged 888 kW. IT energy 7,776 MWh/yr. Total HPC energy 8,037,500 kWh (my arithmetic: PUE ≈ 1.034).
  - Trailing PUE "1.06 or better" since 2014.
  - On-site WUE 0.70 L/kWh with the TSC, vs 1.27 (heat recovery + towers) and 1.42 L/kWh (towers only).
  - 2-yr water saved: 7,950 m3 (2.10 M gal). Energy + water savings $5,455.
  - Water entering the TSC averaged 28.9 C (84 F). The TSC runs harder below 9.4 C (49 F) dry bulb.
  - Colorado EWIF 4.542 L/kWh (from Torcellini 2003); WUE_source 5.4 L/kWh.
- Quotes: "on-site water usage effectiveness (WUE) was 0.70 L/kWh" (p.v). TSC fans run so the water saved "always exceeds the economic value of the extra fan energy" (p.8). The savings came "without negatively impacting the energy-efficient operation" (p.13).
- Note: Measured evidence that a dry stage ahead of towers, on a warm (~29 C) loop in a semi-arid climate, halves on-site water with no visible PUE change (PUE about 1.03–1.06). Annual: supports a small energy penalty for dry operation on warm loops. Peak: the towers still carry the hot hours, so this says nothing about all-dry peaks.

### 3.2 NREL TP-2C00-66690 (2017) — thermosyphon modeling (ASHRAE Winter Conference preprint)
- Citation: Carter T, Liu Z, Sickinger D, Regimbal K, Martinez D. *Thermosyphon Cooler Hybrid System for Water Savings in an Energy-Efficient HPC Data Center: Modeling and Installation*. NREL/TP-2C00-66690, 2017.
- URL: https://www.nrel.gov/docs/fy17osti/66690.pdf (read via docs.nlr.gov)
- Type: government lab with Johnson Controls, modeled. Read.
- Numbers:
  - $0.07/kWh, water $6.08/kgal. Load 0.910 MW.
  - Modeled makeup water 8,300 m3 (2.2 M gal) with towers only vs 3,700 m3 with the hybrid, a 56% saving. Annual utility cost down 40%.
  - TSC carries the full load below 9.4 C (49 F) dry bulb, about 50% of the year in Golden.
  - On hot days coincident wet bulb is 11–22 C (20–40 F) below dry bulb. Per unit air, a tower removes about 380% more heat than a dry coil for a 10 F change (p.3).
- Quote (p.3): air-cooled heat exchangers "usually are quite large in plan area" but "require no water".
- Note: The physics behind the hot-hour gap is the dry-bulb vs wet-bulb sink difference. Fan energy is set by the cost of water, not by need.

### 3.3 Karimi et al. 2022, Resources, Conservation and Recycling (Phoenix, measured)
- Citation: Karimi L, Yacuel L, Degraft-Johnson J, Ashby J, Green M, Renner M, Bergman A, Norwood R, Hickenbottom KL. Water-energy tradeoffs in data centers: A case study in hot-arid climates. *Resour. Conserv. Recycl.* 181:106194 (2022). doi:10.1016/j.resconrec.2022.106194
- URL: https://experts.arizona.edu/en/publications/water-energy-tradeoffs-in-data-centers-a-case-study-in-hot-arid-c/
- Type: peer-reviewed. Abstract via WebFetch; full text paywalled, not read.
- Numbers (paraphrase of abstract): two Phoenix colocation sites.
  - DC1 uses air-cooled chillers; DC2 uses water-cooled chillers plus evaporative cooling.
  - DC1's average PUE is about 13% higher, but its source WUE is 66% lower.
  - Free and evaporative cooling are usable about 40% of the year.
- Han et al. (arXiv 2603.02705, Fig. 1b) re-plots monthly 2019 PUE for a 54 MW dry-cooler site and a 34.5 MW tower site from this study.
- Note: Real hot-arid data. A 13% PUE gap in Phoenix is above the model's 4.8% for Dallas. Phoenix is hotter and these are chilled-water/colo designs, so the gap is consistent in direction and plausibly in size. Annual.

### 3.4 Karimi et al. 2025, Applied Thermal Engineering (Phoenix, 8760-h model)
- Citation: Karimi L, Shinh R, Laisure-Pool C, Green M, Yacuel L, Ashby J, Hickenbottom KL. Energy and water dynamics in data center cooling: Insights from a modeling study in hot-arid climates. *Appl. Therm. Eng.* 276:126802 (2025). doi:10.1016/j.applthermaleng.2025.126802
- URL: https://experts.arizona.edu/en/publications/energy-and-water-dynamics-in-data-center-cooling-insights-from-a-/
- Type: peer-reviewed. Abstract via WebFetch; full text paywalled, no PUE values read.
- Numbers (paraphrase of abstract):
  - Air-cooled chillers use the most energy and source water. Water-cooled chillers use the most on-site water.
  - Air-side economizing saves about 22% of energy and source water for air-cooled chillers, and 29% of on-site water for water-cooled.
  - Pre-cooling air-cooled chillers saves 11% of energy.
  - Evaporative cooling with economizing covers 64% of the year.
- Note: Confirms direction. Exact PUEs need the paywalled text.

### 3.5 Vertiv white paper, *Calculating the Impact of Water Usage on Data Center Costs and Sustainability* (2020)
- Citation: Vertiv Group Corp., SL-70704 (R11/20).
- URL: https://www.vertiv.cn/4ad73a/globalassets/documents/white-papers/vertiv-water-usage-and-sustainability-wp-en-na-web_317594_0.pdf
- Type: maker white paper. Read.
- Numbers (3 MW, Ashburn VA):
  - Air-cooled chiller with free-cooling economization: pPUE 1.13, WUE 0.
  - Adding adiabatic misting improves pPUE by about 0.01 (208,000 kWh/yr) and raises WUE from 0 to 0.165 L/kWh (4.3 M gal/yr).
  - Indirect evaporative is another ~0.02 better than adiabatic (572,791 kWh/yr). That is 18% less energy than the adiabatic system and 24% less than the plain air-cooled chiller system.
  - DX with pumped refrigerant: pPUE 1.12, no water.
  - Air-cooled chillers have "a larger peak load than the adiabatic option" (paraphrase).
  - Cites Argonne 2017 for 0.576 gal/kWh as the U.S. average water consumption of electricity.
- Note: For Loudoun, evaporative help is worth only about 0.01–0.03 of annual PUE over a dry free-cooling chilled-water plant. That is smaller than the model's 0.042 at 23 C, but Vertiv's comparison is adiabatic or indirect evaporative, not open towers. Peak: qualitative only.

### 3.6 SPX Cooling Tech, *Cooling Towers Offer Water and Energy Savings as Part of Efficient Data Center Cooling Systems* (WP-DC-26, issued 04/2026)
- Citation: Mortensen K (SPX Cooling Tech), summarizing Chiddix T and Zion B (Swanson Rink), "Data Center Water Usage for Denver, Phoenix and Los Angeles: A Look at the big picture."
- URL: https://spxcooling.com/wp-content/uploads/WP-DC-26.pdf
- Type: maker (tower vendor) white paper. Read.
- Setup: 1,500 kW steady cooling load, standard-efficiency chillers, no economizer.
- Numbers:
  - Full-load chiller kW/ton: air-cooled 1.250 / 1.340 / 1.250 vs water-cooled 0.431 / 0.462 / 0.426 (Denver / Phoenix / LA).
  - Annual kWh: air-cooled 4,663,470 / 4,999,089 / 4,663,470 vs water-cooled 1,610,748 / 1,726,603 / 1,592,062.
  - Power-plant water (from NREL TP-550-33906): CO 1.20, AZ 7.88, CA 4.64 gal/kWh. With these, air-cooled shows 22.6–59% more total water.
  - Free cooling cuts energy "typically by 75 percent or more" (paraphrase).
- Note: This is the kind of no-economizer, compressor-all-year comparison behind "air-cooled uses ~3x the cooling energy" claims. My arithmetic: about +0.35 vs +0.12 pPUE. It does not represent a 23 C loop or economizing chilled-water plants. Its total-water conclusion depends on hydro-inclusive state EWIFs (AZ 7.88).

### 3.7 ACHR News, "Water-Cooled Technology Cuts Costs" (June 9, 2014), analysis supplied by Baltimore Aircoil
- URL: https://www.achrnews.com/articles/126831-water-cooled-technology-cuts-costs
- Type: trade press, vendor-supplied. Page via WebFetch.
- Numbers: 500-ton plants, office-type load.
  - Peak demand 345 kW water-cooled vs 628 kW air-cooled (45% lower).
  - Annual 629,937 vs 1,195,258 kWh (47% lower).
  - Chillers 0.6 vs 1.255 kW/ton full load; 0.4 vs 0.941 IPLV.
- Note: Peak plant demand nearly 1.8x for air-cooled chilled water, comfort-cooling basis. Relevant to the model's chilled-water case (+11% total facility, +44% overhead at peak).

### 3.8 Mokkapati & Das (2026), engrXiv preprint — adiabatic vs dry, 12 U.S. cities
- Citation: Mokkapati V (Nimbus Advanced Process Cooling), Das DK. When Does Adiabatic Cooling Outperform Dry Cooling? A Twelve-City U.S. Data-Center Siting Assessment at ASHRAE Design Conditions. Preprint submitted to *Energy and Buildings*, 28 July 2026. Not peer reviewed.
- URL: https://engrxiv.org/preprint/download/7795/12658/10948
- Type: preprint, authors' firm sells adiabatic coolers. Read.
- Scope: 10 MW, 107 F (41.7 C) leaving fluid, ASHRAE W3 class. Heat-rejection subsystem only; no chillers or PUE.
- Numbers:
  - Adiabatic cuts heat-rejection electricity by a median of 30.5% (max 41%). Trade ratio 8–56 gal (30–210 L) of on-site water per kWh saved.
  - Dry cooling cannot reach 107 F at Phoenix, Las Vegas (all design points) or Tucson 0.4%.
  - El Paso dry banks use 646–841 MWh/yr. My arithmetic: 0.74–0.96% of heat rejected, so heat-rejection fans add about 0.007–0.010 to PUE.
  - Uses Macknick factors × eGRID2023 for grid water: U.S. ≈ 0.5 gal/kWh; AZNM ≈ 0.43; NWPP ≈ 1.93 gal/kWh.
  - Hydro allocation is called "methodologically contested" (paraphrase).
- Note: On a warm (W3) loop, dry-cooler fan energy is under 1% of IT energy, even in El Paso. Water spent to save that electricity is about 10x the upstream water saved. Annual. Peak: dry is infeasible above about the target temperature minus the approach.

### 3.9 LBNL 2024 United States Data Center Energy Usage Report
- Citation: Shehabi A, Smith SJ, Hubbard A, Newkirk A, Lei N, Siddik MAB, Holecek B, Koomey J, Masanet E, Sartor D. *2024 United States Data Center Energy Usage Report*. LBNL-2001637, December 2024.
- URL: https://eta-publications.lbl.gov/sites/default/files/2024-12/lbnl-2024-united-states-data-center-energy-usage-report.pdf (redirects to escholarship; read from mirror https://legalectric.org/f/2025/09/lbnl-2024-united-states-data-center-energy-usage-report_1.pdf)
- Type: government lab. Read (pp. 43–57).
- Numbers:
  - Indirect water: data centers 4.52 L/kWh (2023), U.S. average electricity 4.35 L/kWh. Nearly 800 billion L indirect for 176 TWh.
  - Direct (site) fleet WUE just over 0.36 L/kWh through 2023, rising to 0.45–0.48.
  - Hyperscale systems report 0.1–0.3 L/kWh.
  - Factors are by balancing authority from EIA-930/923 (Siddik et al. 2024). PUE/WUE ranges by cooling type appear only in Fig. 4.4.
- Quotes:
  - "While air-cooled chillers use no water, they use more energy." (p.45)
  - "national average of 4.52 L/kWh of indirect water consumption" (p.57)
  - "the average water intensity factor for electricity use in the U.S. overall is 4.35 L/kWh" (p.57)
- Note: The national indirect factor is large (1.15 gal/kWh) because it includes hydro reservoir evaporation. It should not be applied to MI/VA/TX without the regional factor.

### 3.10 Lei, Lu, Shehabi, Masanet (2025) — water footprint of workloads
- Citation: Lei N, Lu J, Shehabi A, Masanet E. The water use of data center workloads: A review and assessment of key determinants. *Resour. Conserv. Recycl.* 219 (2025). Preprint: Research Square rs-4159702.
- URL: https://assets-eu.researchsquare.com/files/rs-4159702/v1_covered_0dc375a0-6402-41e1-9834-84e85ed3c44a.pdf
- Type: peer-reviewed (preprint read).
- Content: eight cooling archetypes. Air-cooled chiller and DX sites have lower WUE-site but "typically have higher PUE values due to lower chiller coefficient of performance" (p.~13, paraphrase-length quote).
- Numbers: in figures only, not extractable from text.
- Note: Qualitative support. For PUE by cooling type and climate, the paywalled Lei & Masanet 2022 (*RCR*) is the source to obtain; not found open.

### 3.11 Schneider Electric White Paper 220, *Water Usage at AI Scale* (2026) — secondary only
- Citation: Schneider Electric (S. Carlini). 100 MW AI facility, Dallas vs Paris; reference designs (RD113DS).
- Read via: TechTarget, Snider S., "AI data centers can run hot to stay cool: report," Sept 24, 2026. https://www.techtarget.com/it-infrastructure/news/366651212/AI-data-centers-can-run-hot-to-stay-cool-report (page via WebFetch). Schneider PDFs returned HTML; not read.
- Type: maker white paper, via trade press.
- Numbers:
  - Raising the TCS from 32 C to 45 C cuts WUE about 66% (Dallas) and 82% (Paris), with PUE gains < 1%.
  - Chiller assist starts at about 35 C outdoor (45 C design) vs about 25 C (32 C design).
  - Dallas ambient −9 to 39 C. Paris adiabatic assist improves PUE by an average of 0.13% and adds 0.07 L/kWh.
  - Air to 32 C liquid in Dallas: PUE about 7% better.
  - One summary cites Dallas PUE 1.148 (air/evaporative) vs 1.04 (liquid). Snippet, unverified.
- Note: With warm loops, adding evaporation changes annual PUE by a fraction of a percent. The model's 23 C shared loop is much colder than 32–45 C TCS loops. That is likely why the model's dry penalty (0.04–0.06) is larger than Schneider's.

### 3.12 Uptime Institute Briefing Report 200 (April 24, 2026) — paywalled
- Citation: Talib R, Dietrich J. "Dry cooling energy performance can rival evaporative cooling." Uptime Intelligence.
- URL: https://intelligence.uptimeinstitute.com/resource/dry-cooling-energy-performance-can-rival-evaporative-cooling
- Type: industry research on operating-site data. Summary page via WebFetch; report paywalled.
- Claim (paraphrase): well-designed dry and adiabatic systems can match evaporative PUE across ASHRAE climate zones 2–6. PUE/WUE spread within each system type is wide, and design and operation matter more than category. No numbers visible.
- Note: Counter-evidence to large annual gaps. Supports the view that a 0.04–0.06 PUE gap is a design-dependent upper-middle value, not a law.

### 3.13 EPRI, *Water Usage in Data Centers* — Technology Innovation Spotlight (May 2025)
- Citation: EPRI 3002033251.
- URL: https://restservice.epri.com/publicdownload/000000003002033251/0/Product
- Type: EPRI (utility research). Read.
- Numbers:
  - 150 MW example: water-cooled chiller at WUE 2.8 L/kWh, about 2.7 MGD (970 M gal/yr). IT liquid cooling with dry coolers at WUE 0.2 L/kWh, about 190,000 gal/d.
  - Says air-cooled chillers are less energy efficient (paraphrase). No PUE values.
- Note: The WUE of 2.8 L/kWh implies about 1.8 MGD per 100 MW (my arithmetic), 3.3x the model's Loudoun 0.54 MGD. The model sits between EPRI's tower example and NREL ESIF's measured 1.42 L/kWh (≈ 0.90 MGD per 100 MW). Siddik 2021 uses 1.8 m3/MWh direct (≈ 1.14 MGD per 100 MW). The model's 0.85 L/kWh-IT annual is plausible for Loudoun with winter economizing, but at the low end of published values.

### 3.14 Han, Li, Wierman, Ren (2026), arXiv 2603.02705 — "Small Bottle, Big Pipe"
- URL: https://arxiv.org/pdf/2603.02705 (v2, 18 Mar 2026)
- Type: preprint (academic). Read.
- Content (paraphrase):
  - Industry disclosures say water-cooled sites use 25–35% less electricity than air-cooled, especially in summer (citing Amazon and the Water-AI Nexus report).
  - Google's 2025 Environmental Report: a Nevada site relying mainly on non-evaporative cooling has 6.4–10.2% higher annual PUE than the same company's evaporative site.
  - Dry-cooler summer PUE can be well above the annual average, especially in hot climates.
- Note: Points to Google's Nevada pair as a real-world annual check (see 6.4).

---

## 4. Peak demand

- PNNL-26917 curves (1.2): air-cooled kW per kW of cooling is about 1.24–1.33x rated at 110–115 F, with capacity 0.885–0.915 of rated. The penalty grows on exactly the hours that set grid peaks.
- ACHR/BAC 2014 (3.7): air-cooled plant peak 628 kW vs 345 kW water-cooled for 500 tons.
- Data Center Knowledge (snippet, unverified): a Mid-Atlantic 103 F peak case with a traditional air-cooled chiller at 1.17 kW/ton vs 0.84 kW/ton for a magnetic-bearing air-cooled chiller (29%). URL: https://www.datacenterknowledge.com/node/165477
- Vertiv (3.5): air-cooled units have a larger peak load than the adiabatic option (qualitative).
- Amazon (6.1): 25–35% operational energy reduction "during peak summer periods".
- Grid planners: NERC 2026 Summer Reliability Assessment coverage (Utility Dive) discusses large-load behavior and forecasting. It cut ERCOT's 2026 summer demand forecast by about 1.9 GW for large-load modeling; another outlet says 3.7 GW (conflicting, snippet, unverified). No source found that quantifies data-center cooling load vs temperature (ERCOT, PJM, EPRI, NERC). URLs: https://www.utilitydive.com/news/demand-management-data-center-flexibility-boost-regional-reliability-nerc/821225/ ; https://texasre.org/Documents/Presentations/Talk%20with%20Texas%20RE/2026/Talk%20with%20Texas%20RE%20-%20Summer%20Reliability%20Assessment%20-%20May%2026%2C%202026.pdf (not read).
- Gap: no grid-planning document gives a temperature coefficient for data-center load.

---

## 5. Grid water intensity (consumption per kWh)

### 5.1 WRI 2020 — eGRID subregion factors
- Citation: Reig P, Luo T, Christensen E, Sinistore J. *Guidance for Calculating Water Use Embedded in Purchased Electricity*. WRI Working Paper, January 2020. Data: thinkstep/GaBi 2018. Models 68% recirculating and 32% once-through cooling nationally.
- URL: https://files.wri.org/d8/s3fs-public/guidance-calculating-water-use-embedded-purchased-electricity.pdf
- Type: NGO working paper (LCA database). Read (Appendix 1, p.15).
- Consumption factors (gal/kWh; L/kWh my arithmetic):

  | eGRID subregion | Withdrawal | Consumption | L/kWh |
  |---|---|---|---|
  | RFCM (RFC Michigan) | 44 | 0.66 | 2.50 |
  | MROE (MRO East) | 85 | 0.81 | 3.07 |
  | SRVC (SERC Virginia/Carolina) | 39 | 0.63 | 2.38 |
  | ERCT (ERCOT All) | 9 | 0.34 | 1.29 |
  | AZNM (WECC Southwest) | 184 | 1.31 | 4.96 |
  | United States (App. 2) | 102 | 0.83 | 3.14 |

### 5.2 Torcellini, Long, Judkoff (2003), NREL/TP-550-33905
- Citation: *Consumptive Water Use for U.S. Power Production*. NREL/TP-550-33905, Dec 2003. This is the EWIF source used by The Green Grid WUE_source and by NREL ESIF.
- URL: https://www.nrel.gov/docs/fy04osti/33905.pdf (read via docs.nlr.gov)
- Type: government lab. Read (Tables 2–3).
- Per kWh of end-use (site) energy, states assumed not to trade power, hydro reservoir evaporation included. Weighted total gal/kWh:
  - Michigan 0.48 (thermoelectric 0.50)
  - Virginia 0.06 (thermo 0.07)
  - Texas 0.43
  - Arizona 7.85 (thermo 0.32, hydro 64.85)
  - Colorado 1.20
  - U.S. 2.00 (thermo 0.47, hydro 18.27)
  - Interconnects: Eastern 2.33, Western 4.42, Texas 0.43
- Quote (p.4): states not trading power is "a poor assumption, but typically used".
- Note: Old (1990s data). Virginia's 0.06 looks implausibly low against WRI's 0.63. Arizona's 7.85 is hydro-driven. The SPX white paper uses a sibling report (TP-550-33906) with the same AZ/CA/CO values.

### 5.3 Siddik, Shehabi, Marston (2021), Environ. Res. Lett.
- Citation: Siddik MAB, Shehabi A, Marston L. The environmental footprint of data centers in the United States. *Environ. Res. Lett.* 16:064017 (2021). doi:10.1088/1748-9326/abfba1
- URL: https://iopscience.iop.org/article/10.1088/1748-9326/abfba1/pdf
- Type: peer-reviewed (open access, CC BY). Read.
- Numbers:
  - Total (direct + indirect) 7.1 m3/MWh national. Range 1.8–105.9 m3/MWh by subbasin (Fig. 4, map only).
  - About three-quarters of the operational water footprint is indirect.
  - Direct water uses 1.8 m3/MWh. Table 1 gives 7.0–7.2 m3/MWh by data-center type.
  - Factors are assigned by power control area from EIA plant data, with Macknick factors for unreported plants and reservoir evaporation assigned to hydropower.
- Gap: no per-region numeric table in the paper text. Regional values are in the map or SI only.

### 5.4 Macknick, Newmark, Heath, Hallett (2012), Environ. Res. Lett. 7:045802
- URL: https://iopscience.iop.org/article/10.1088/1748-9326/7/4/045802
- Type: peer-reviewed (NREL). Page via WebFetch (Tables 1–2); PDF download blocked.
- Median operational consumption (gal/MWh):
  - NGCC tower 205, NGCC dry 2
  - Coal subcritical tower 479 (Mokkapati & Das cite 687 for generic coal tower)
  - Nuclear tower 672
  - CSP trough tower 906, dry 78
  - Utility PV 1, wind 0
- Note: Technology factors for building regional EWIFs. Gas-heavy grids (ERCOT, PJM-VA) sit near 0.2–0.5 gal/kWh before hydro.

### 5.5 Other national figures
- LBNL 2024 (3.9): U.S. 4.35 L/kWh (1.15 gal/kWh); data-center weighted 4.52 L/kWh, including hydro.
- Argonne 2017, as cited by Vertiv (3.5): U.S. 0.576 gal/kWh (2.18 L/kWh). Primary not read.
- Mokkapati & Das (3.8): about 0.5 gal/kWh U.S. (Macknick × eGRID2023); AZNM about 0.43 gal/kWh. Compare WRI AZNM 1.31; the difference is hydro and method.

### 5.6 What this means for the dry vs tower water balance (my arithmetic)
- Loudoun: the dry penalty of 0.042 PUE × 100 MW × 24 h is about 100.8 MWh/day.
- Indirect water saved by choosing towers instead of dry, per day:
  - WRI SRVC (0.63 gal/kWh): about 0.064 MGD
  - LBNL U.S. (1.15 gal/kWh): about 0.116 MGD
  - Torcellini VA (0.06 gal/kWh): about 0.006 MGD
- Tower on-site consumption is about 0.54 MGD, so towers use about 5–90x the water they save at the power plant in Virginia.
- Under the same assumptions, the break-even grid factor for Loudoun is about 5.4 gal/kWh. Only hydro-inclusive Western factors (AZ 7.85 in Torcellini) come close. This is the logic of the SPX/Swanson Rink and Karimi source-WUE results, which flip only on Western hydro-heavy factors.

---

## 6. Public claims to test

### 6.1 Amazon, "FAQ: Why does AI use water?" (Oct 2, 2025)
- URL: https://sustainability.aboutamazon.com/stories/just-back-from-weftec-why-does-ai-use-water
- Type: company statement. Page via WebFetch.
- Claim: evaporative systems "can reduce operational energy use between 25% and 35% during peak summer periods". Footnote: results vary by location and climate. Baseline (total facility or cooling only) not stated.
- Test vs model: hottest-hour total facility gap is 5.5–8.7%, and 34–38 vs 27 MW of non-IT overhead (+26–41%). The claim matches the model if read as cooling or overhead energy, not total.

### 6.2 Data Center Knowledge, "Can Evaporative Cooling in Data Centers Still Make Sense?" (Patrizio A, Oct 23, 2026)
- URL: https://datacenterknowledge.com/cooling/can-evaporative-cooling-in-data-centers-still-make-sense-
- Type: trade press, quoting vendors. Page via WebFetch.
- Claims (paraphrase):
  - Capture H2O CEO: water-cooled systems are about 25–40% more energy efficient than closed-loop air-cooled.
  - ServerLIFT's quality manager: evaporative can use 10–35% less electricity in peak summer.
- Test: same as 6.1. Plausible for cooling energy at peak, not for total facility energy, and not for annual totals on warm loops.

### 6.3 Google — Hölzle U, "Our commitment to climate-conscious data center cooling" (Nov 21, 2022)
- URL: https://blog.google/outreach-initiatives/sustainability/our-commitment-to-climate-conscious-data-center-cooling/
- Type: company statement. Page via WebFetch.
- Claim (paraphrase): water-cooled data centers use about 10% less energy and emit about 10% less carbon than many air-cooled ones.
- Google 2023 Data Center Water Risk Framework (read): air-cooled chillers "consume more energy and typically have a higher carbon footprint"; Mesa AZ will be air-cooled. https://www.gstatic.com/gumdrop/sustainability/2023-data-center-water-risk-framework-whitepaper.pdf
- Snippet, unverified: Google's Koley said air cooling uses about 10% more energy on average and about twice that on a hot day. Axios, June 3, 2026, returned 403.
- Test: the model's annual total gap of 3.3–4.8% is below Google's 10% fleet figure. Google's air-cooled sites are mostly chiller or DX designs in hot places (Mesa, Nevada), so a warm-loop dry-cooler design should come in lower.

### 6.4 Google campus PUE (datacenters.google/efficiency), 2026 Q1 / Q2 (quarterly / TTM)
- URL: https://datacenters.google/efficiency
- Type: company-reported measured data. Page via WebFetch.
- Values:
  - Henderson NV (evaporative per Google): 1.08 / 1.09 and 1.10 / 1.09
  - Storey County NV (described as air-cooled in press; not confirmed in a primary Google doc): 1.11 / 1.15 and 1.17 / 1.15
  - Mesa AZ (air-cooled per Google 2023 framework): 1.22 and 1.28 quarterly, no TTM yet
  - Loudoun VA: 1.07–1.09 / 1.08
  - Midlothian TX: 1.08–1.12 / 1.10–1.11
- My arithmetic: the TTM gap between Storey and Henderson is +0.06 (≈ 5.5%). The arXiv preprint cites 6.4–10.2% from Google's 2025 report.
- Note: The best measured annual check found. A same-operator dry vs wet pair in one state differs by about 0.06 PUE. The model's 0.042–0.057 sits right there. Mesa's summer quarter (1.28) shows the hot-climate seasonal peak.

### 6.5 Microsoft — Solomon S, "Sustainable by design: Next-generation datacenters consume zero water for cooling" (Dec 9, 2024)
- URL: https://microsoft.com/en-us/microsoft-cloud/blog/2024/12/09/sustainable-by-design-next-generation-datacenters-consume-zero-water-for-cooling
- Type: company statement. Page via WebFetch.
- Claim (paraphrase): replacing evaporative with mechanical cooling raises PUE, but fleet annual energy rises only "nominally". It avoids more than 125 M L/yr per datacenter. Pilots in Phoenix and Mt. Pleasant, WI, in 2026.
- Note: An operator calls the annual penalty small. Consistent with a few percent.

### 6.6 KSL.com, Anderson M., "Closed-loop cooling systems save water but can be a drain on electricity" (May 12, 2026)
- URL: https://www.ksl.com/article/51496230
- Type: local press. Page via WebFetch.
- Content: no percentage in the article text; the search snippet's "10–40%" was not found on the page. Quotes a University of Utah professor that summer closed-loop needs water or a power-hungry compressor (paraphrase).

---

## Summary against the model

- Annual. The evidence brackets the model's dry-minus-tower gap of 0.038–0.057 PUE (3.3–4.8%):
  - Low end: Uptime (parity in zones 2–6, paywalled); Schneider WP220 (< 1% with 45 C loops); NREL ESIF (no visible PUE change, warm loop, hybrid); Mokkapati & Das (dry fans < 1% of IT energy at W3).
  - Middle: Vertiv Ashburn (0.01–0.03 pPUE over a free-cooling air-cooled chilled-water plant); Microsoft ("nominal"); Google Nevada pair (+0.06, about 5.5%; 6.4–10.2% per Google's 2025 report).
  - High end: Google fleet claim (~10%); Karimi Phoenix (+13%); SPX/BAC no-economizer chilled-water cases (cooling energy 2–3x).
  - The model's 23 C loop sits between warm-liquid (32–45 C) designs and 7–13 C chilled water, so its mid-range placement is reasonable.
- Peak:
  - Code curves (PNNL-26917) put air-cooled kW per kW of cooling at about 1.24–1.33x rated at 110–115 F, with 9–12% less capacity.
  - Vendor comparisons give air-cooled chilled-water plant peaks about 1.8x water-cooled.
  - The model's Dallas chilled-water gap (149 vs 134 MW) looks small next to code-minimum arithmetic (~20–25 MW). Check the rated COP and the hottest-hour ambient.
  - The 23 C-loop hot-hour gap of 7–11 MW per 100 MW is consistent with "25–35% of cooling energy at peak" public claims.
- Water:
  - Regional consumption factors: RFCM 0.66, MROE 0.81, SRVC 0.63, ERCT 0.34, AZNM 1.31 gal/kWh (WRI 2020). Torcellini 2003: MI 0.48, VA 0.06, TX 0.43, AZ 7.85.
  - National: 4.35 L/kWh (LBNL 2024, hydro-inclusive) vs about 0.5–0.83 gal/kWh (Macknick/eGRID, WRI).
  - At these factors, in MI/VA/TX towers' on-site consumption far exceeds the power-plant water saved. Only hydro-heavy Western factors reverse that.

## Gaps and access notes
- Paywalled or not read: Karimi 2025 full text; Karimi 2022 full text; Lei & Masanet 2022 (*RCR*); Uptime BR-200; Schneider WP220 and WP132 primary PDFs (se.com returned HTML); the WRI data appendix (download behind a webform, not submitted).
- Not found: a numeric maker table for air-cooled chiller capacity and kW/ton at 105–115 F (Trane, Carrier, York, Daikin); a pump-head comparison for glycol dry-cooler vs tower loops; Güntner, Alfa Laval and EVAPCO fan kW per kW (EVAPCO's data-center brochure has no numbers); Johnson Controls BlueStream fan data; grid-planner temperature coefficients for data-center load.
- nrel.gov no longer resolves (NREL docs moved to docs.nlr.gov, which blocks plain curl). The NREL PDFs were obtained through the fetch tool. 72196 was fetched once with a browser User-Agent before such requests were stopped.
