# Dry vs evaporative cooling: energy evidence (sources and operator disclosures)

Compiled Nov 16, 2026 for the Water Ledger methods review. Downloaded files: `scratchpad/dl-operators/` (PDFs, text extracts, rendered figure pages).

Model being checked (Water Ledger, shared ~23 C facility loop, year-average PUE, dry vs towers):
Grand Rapids 1.175 vs 1.137 (dPUE 0.038, +3.3%); Loudoun 1.192 vs 1.150 (0.042, +3.7%); Dallas 1.233 vs 1.176 (0.057, +4.8%); Dallas chilled water 7-13 C 1.351 vs 1.268 (0.083, +6.5%).

Labels: **[V]** read in the primary document; **[F]** read off a figure by eye (about +/-0.02 PUE); **[S]** search snippet only, unverified; **[D]** derived by me from disclosed numbers.

---

## 1. LBNL 2024 United States Data Center Energy Usage Report

- **Citation:** Shehabi, A., Smith, S.J., Hubbard, A., Newkirk, A., Lei, N., Siddik, M.A.B., Holecek, B., Koomey, J., Masanet, E., Sartor, D. (Dec 2024). *2024 United States Data Center Energy Usage Report.* LBNL-2001637. Lawrence Berkeley National Laboratory.
- **URL:** https://eta-publications.lbl.gov/sites/default/files/2024-12/lbnl-2024-united-states-data-center-energy-usage-report.pdf. The LBL link returned 403 to scripts; I used the eScholarship copy, https://escholarship.org/content/qt32d6m0d1/qt32d6m0d1.pdf.
- **Type:** government lab report.
- **Structure:** The report has no PUE/WUE tables by cooling type. Table 4.2 (p. 40-42) defines the nine cooling systems. Table 4.3 (p. 43) gives the assumptions:
  - UPS efficiency 90-99% for hyperscale and AI.
  - ASHRAE A2 envelope for hyperscale.
  - Liquid-cooled AI in class **W45**, which means facility water up to 45 C.
  - The values are box plots in **Figure 4.4 (p. 46)**: simulated annual PUE and site WUE across 965 TMY stations, with 50 scenarios per case. The box spans the 25th-75th percentile; I read the median line.
- **Key numbers [F], median annual PUE (box range):**

| Space type | Cooling system | PUE median (IQR) | WUE site median, L/kWh |
|---|---|---|---|
| Midsize | Air-cooled chiller | ~1.83 (1.72-1.96) | ~0.05 |
| Midsize | Water-cooled chiller (tower) | ~1.52 (1.47-1.58) | ~2.9 |
| Midsize | Dry cooler (air-cooled chiller) | ~1.58 (1.49-1.69) | ~0.05 |
| Midsize | Waterside economizer (water-cooled chiller) | ~1.37 (1.32-1.43) | ~2.5 |
| Midsize | Airside economizer (air-cooled chiller) | ~1.57 | ~0.02 |
| Midsize | Airside economizer (water-cooled chiller) | ~1.45 | ~1.3 |
| Large-scale | Dry cooler + adiabatic assist (air-cooled chiller) | ~1.20 (1.16-1.24) | ~0.25 |
| Large-scale | Airside econ + adiabatic (air-cooled chiller) | ~1.17 (1.13-1.21) | ~0.02 |
| Large-scale | Airside econ + adiabatic (water-cooled chiller) | ~1.14 (1.11-1.18) | ~0.4 |
| Large-scale | Waterside economizer (water-cooled chiller) | ~1.12 (1.10-1.15) | ~2.2 |
| Large-scale, IT liquid | Waterside economizer (water-cooled chiller) | ~1.13 (1.10-1.17) | ~2.0 |
| Large-scale, IT liquid | Dry cooler + adiabatic (air-cooled chiller) | ~1.10 | ~0.15 |
| Large-scale, IT liquid | Dry cooler (air-cooled chiller) | ~1.09-1.10 (1.07-1.12) | ~0 |

- **Other numbers [V]:**
  - US average PUE was 1.6 in 2014 and 1.4 in 2023, and is projected at 1.15-1.35 in 2028 (p. 47).
  - US average site WUE was about 0.36 L/kWh through 2023, rising to 0.45-0.48 (p. 48).
- **Quotes [V]:**
  - On the trade-off (p. 45): "there are tradeoffs between low PUEs and low site WUEs."
  - p. 45: "While air-cooled chillers use no water, they use more energy."
  - On the hyperscale adiabatic case (p. 46-47): "Some hyperscale facilities report WUE values for similar systems of 0.1-0.3 L/kWh". This is higher than the modeled value.
  - p. 44: "simulated PUEs assume systems are commissioned and operate as designed."
- **Dry vs evaporative:**
  - Air-cooled IT, midsize: dry costs about +0.2 to +0.3 PUE.
  - Air-cooled IT, large-scale: dry costs about +0.03 (airside adiabatic, air-cooled vs water-cooled chiller backup) to +0.08 (dry+adiabatic vs waterside economizer).
  - Liquid-cooled IT at W45: dry coolers come out *equal or slightly lower* in PUE than towers.
  - The results are annual only, with no peak values. Climate appears only as spread; there are no per-city values.

## 2a. Lei and Masanet 2022, RCR 182:106323

- **Citation:** Lei, N., Masanet, E. (2022). Climate- and technology-specific PUE and WUE estimations for U.S. data centers using a hybrid statistical and thermodynamics-based approach. *Resources, Conservation & Recycling* 182, 106323. doi:10.1016/j.resconrec.2022.106323.
- **URL:** The ScienceDirect page returned 403. I used the open preprint (CC BY), Research Square rs-769999: https://www.researchsquare.com/article/rs-769999/latest.pdf.
- **Type:** peer-reviewed (I read the preprint version).
- **Structure:** 10 cases (Table 2) in 16 IECC/ASHRAE climate zones, each with a representative city and TMY weather. Figure 4 (preprint p. 18) shows annual PUE by case and zone as an image.
- **Key numbers [V]:**
  - Median PUE is 1.12-1.25 for large-scale (cases 1-2), 1.39-1.98 for midsize (cases 3-7) and 1.71-2.22 for small (cases 8-10).
  - Highest PUE is in 1A, lowest in 8.
- **Key numbers [F], read from Fig. 4 medians:**
  - Midsize water-cooled chiller with no economizer (case 5) is ~1.63-1.67 in every zone, so it is almost climate-flat.
  - Midsize air-cooled chiller with no economizer (case 7):
    - 1A ~1.98
    - 2B ~1.99 (Phoenix-type)
    - 3A ~1.80 (Dallas-type)
    - 4A ~1.74 (Virginia-type)
    - 5A ~1.69 (Michigan-type)
    - 8 ~1.58
  - Penalty of the air-cooled chiller over the water-cooled chiller at midsize: 5A ~+0.06, 4A ~+0.10, 3A ~+0.15, 2B ~+0.33.
  - Midsize waterside economizer (case 4) is ~1.40-1.45. Midsize airside economizer with air-cooled chiller (case 6) is ~1.53 (5A), ~1.55 (4A), ~1.64 (3A) and ~1.80 (2B).
  - Large-scale cases 1-2 (evaporative) are ~1.13-1.25. The paper has **no large-scale dry or air-cooled case**.
- **Quotes [V]:**
  - Sec. 4.2: "air-cooled chillers and direct expansion systems are generally less energy-efficient".
  - Sec. 4.3: "inner-year extreme hot weather conditions could significantly increase a DC's capital cost". The paper treats peak as outside its scope.
- **Dry vs evaporative:** At midsize the air-cooled chiller penalty grows strongly with heat: about +0.06 in a Michigan-type 5A climate and about +0.15 in Dallas-type 3A. The results are annual only.

## 2b. Lei and Masanet 2020, Energy 201:117556

- **Citation:** Lei, N., Masanet, E. (2020). Statistical analysis for predicting location-specific data center PUE and its improvement potential. *Energy* 201, 117556. doi:10.1016/j.energy.2020.117556.
- **URL:** https://doi.org/10.1016/j.energy.2020.117556. Paywalled, with no open copy (Unpaywall: not OA). I read the abstract via Semantic Scholar and IDEAS.
- **Type:** peer-reviewed.
- **Content:** Thermodynamic PUE models with economizer choices, checked against 17 Google and Facebook hyperscale sites. The abstract (Semantic Scholar) says "climate variables and uninterruptible power supply (UPS) efficiencies are the most important parameters". I could not get per-cooling-type numbers.

## 2c. Lei, Lu, Shehabi, Masanet, "The water footprint of data center workloads" (preprint 2024)

- **Citation:** Research Square rs-4159702 v1, Mar 26, 2024. CC BY. https://assets-eu.researchsquare.com/files/rs-4159702/v1_covered_0dc375a0-6402-41e1-9834-84e85ed3c44a.pdf. A later version is in RCR (2025).
- **Type:** peer-reviewed (preprint).
- **Quote [V]** (p. 10): air-cooled systems "typically have higher PUE values due to lower chiller coefficient of performance".
- The paper also says airside economizer plus direct adiabatic gives the lowest PUE and WUE together. It adds that similar PUE/WUE "can be achieved with different combinations" of technology, climate and efficiency.

## 3. Microsoft

### 3a. Zero-water design announcement
- **Citation:** Solomon, S. (Dec 9, 2024). "Sustainable by design: Next-generation datacenters consume zero water for cooling." Microsoft Cloud Blog.
- **URL:** https://www.microsoft.com/en-us/microsoft-cloud/blog/2024/12/09/sustainable-by-design-next-generation-datacenters-consume-zero-water-for-cooling/
- **Type:** company disclosure.
- **Quotes [V]:**
  - "Replacement of evaporative systems with mechanical cooling will increase our power usage effectiveness (PUE)."
  - "The result is a nominal increase in our annual energy usage". The full sentence continues "compared to our evaporative datacenter designs across the global fleet" (wording from the ESR, below).
- **Numbers [V]:**
  - The design avoids >125 million L/yr per datacenter.
  - Fleet WUE was 0.30 L/kWh in FY24, down from 0.49 in 2021.
  - Phoenix and Mt. Pleasant pilots in 2026; designs from Aug 2024; sites online late 2027.
  - **No PUE number** is given for the new design.

### 3b. 2025 Environmental Sustainability Report
- **Citation:** Microsoft (May 2025), covering FY24.
- **URL:** https://cdn-dynmedia-1.microsoft.com/is/content/microsoftcorp/microsoft/msc/documents/presentations/CSR/2025-Microsoft-Environmental-Sustainability-Report.pdf
- **Quotes [V], p. 36:**
  - The report repeats the blog text.
  - Microsoft offsets the extra power "with high-efficiency economizing chillers with elevated water temperatures."
  - "The result is a nominal increase in our annual energy usage".
- No number is given.

### 3c. Efficiency page
- **URL:** https://datacenters.microsoft.com/sustainability/efficiency/
- **Values [V]:**
  - Global PUE 1.16 (FY24) and 1.17 (FY25); WUE 0.30 and 0.27 L/kWh.
  - Americas PUE 1.16 and 1.16; WUE 0.38 and 0.34.
- The page currently shows no per-state values.
- **Per-state values [S], unverified, appeared only in a search snippet:**
  - Arizona PUE 1.18, WUE 1.63.
  - Texas 1.28, 0.25.
  - Virginia 1.14, 0.14.
  - "Design PUE 1.12" for the newest generation.
- The older state fact-sheet PDFs (datacenters.microsoft.com/globe/pdfs/...) now return 404.
- **Fact sheets [S]:** Arizona 2022 PUE 1.223 and WUE 2.24; Virginia 2022 PUE 1.144 and WUE 0.17.

### 3d. Microsoft datacenters in Arizona fact sheet (Oct 2025)
- **URL:** https://local.microsoft.com/wp-content/uploads/2025/10/Microsoft-datacenters-in-Arizona.pdf
- **Quotes [V]:**
  - "DEC uses water for cooling less than 40% of the year."
  - "Future facilities will use air-cooled chillers."
  - Water flows in "when the temperature exceeds 85°F (29.4°C)".
- The PUE/WUE values on the sheet are images and could not be extracted.

### 3e. Inside the world's most powerful AI datacenter (Fairwater, Mt. Pleasant WI)
- **Citation:** Guthrie, S. (Sep 18, 2025). Official Microsoft Blog. https://blogs.microsoft.com/blog/2025/09/18/inside-the-worlds-most-powerful-ai-datacenter/
- **Quotes [V]:**
  - "second largest water-cooled chiller plant on the planet". This refers to a closed loop, not to towers.
  - Heat leaves through "172 20-foot fans".
  - The other 10% of servers use outdoor air, "switching to water only during the hottest days".
- **No PUE or energy statement.**

### 3f. Priest and Solomon (Jun 24, 2026)
- **Citation:** "Inside Microsoft's two-decade push to cut water intensity". https://blogs.microsoft.com/blog/2026/06/24/inside-microsofts-two-decade-push-to-cut-water-intensity-while-scaling-for-growth/
- **Quotes [V]:**
  - On Phoenix: "water use may increase to as much as 40% of the year".
  - Average WUE fell from 2.3 to 0.27 L/kWh in 2025.
- No energy-penalty figure.
- **Microsoft overall:** The energy cost of going water-free is described qualitatively as "nominal" and is never quantified. The company reached its zero-water design through warm-water chip cooling plus economizing air-cooled chillers.

## 4. Google

### 4a. Climate-conscious cooling blog
- **Citation:** Hölzle, U. (Nov 21, 2022). "Our commitment to climate-conscious data center cooling." Google Keyword blog. https://blog.google/outreach-initiatives/sustainability/our-commitment-to-climate-conscious-data-center-cooling/
- **Type:** company disclosure.
- **Quote [V]:** "Water-cooled data centers use about 10% less energy and thus emit roughly 10% less carbon emissions". The base is not defined: it could be facility energy or total energy.

### 4b. Assessing watershed health
- **Citation:** Townsend, B. (Dec 14, 2023). "Assessing watershed health in data center host communities." Google Cloud blog. https://cloud.google.com/blog/topics/sustainability/assessing-watershed-health-in-data-center-host-communities
- **Quotes [V]:**
  - "air-cooling technology, which uses minimal water but consumes more energy."
  - On Mesa AZ: "we opted to air-cool the data center".
  - "Water cooling is generally more energy-efficient than air cooling".

### 4c. Latitude Media article
- **Citation:** Allsup, M. (Mar 13, 2024). "Where does the AI boom leave Google's data center cooling strategy?" Latitude Media. https://www.latitudemedia.com/news/where-does-the-ai-boom-leave-googles-data-center-cooling-strategy/
- **Type:** press.
- **Quotes [V]:**
  - Water cooling "on average uses around 10% less energy than air cooling".
  - On peak days ("ten-odd days per year") air cooling can need "up to 50% more energy" than on an average day. The base is ambiguous: it most likely means cooling energy relative to an average day, not air vs water.
  - Townsend: Mesa "is going to end up with a data center that consumes more energy."

### 4d. Google 2025 Environmental Report (FY2024 data)
- **URL:** https://www.gstatic.com/gumdrop/sustainability/google-2025-environmental-report.pdf
- **Type:** company disclosure. The water table has limited third-party assurance.
- **Sites marked air-cooled [V]:** The water-by-location table (p. 109-110) uses endnote 166, "Air-cooled facility." It applies to Dublin, Montreal, Pflugerville TX, Phoenix AZ, San Bernardo, Storey County NV, Sydney and Wilmer TX.
- **Annual campus PUE, 2024 [V]** (p. 108; earlier years in brackets):

| Campus | Cooling | PUE 2024 [earlier] | Water consumption 2024, Mgal |
|---|---|---|---|
| Council Bluffs IA (1st) | evaporative | 1.11 [1.11 in 2023] | 1,010.2 (whole campus) |
| The Dalles OR (1st) | evaporative | 1.10 | 361.4 (whole campus) |
| Mayes County OK | evaporative (photo of towers, p. 69) | 1.11 | 833.2 |
| Midlothian TX | evaporative | 1.10 [1.16 in 2022, 1.13 in 2023] | 182.3 |
| Henderson NV | evaporative | 1.09 [1.08 in 2023] | 207.4 |
| Loudoun VA (1st / 2nd) | evaporative | 1.09 / 1.08 | Leesburg 191.6; Ashburn 56.0; Sterling 158.2 |
| **Storey County NV** | **air-cooled** | **1.16 [1.19 in 2023]** | **1.5** |
| **Dublin IE** | **air-cooled** | **1.08** | **0.1** |
| Fleet | | 1.09 | 7,787 total |

- **Quarterly PUE, Q1/Q2 2026 [V]** (Google efficiency page, https://datacenters.google/efficiency/):
  - Mesa AZ (air-cooled, <12 months of data so no TTM): **1.22 (Q1), 1.28 (Q2)**
  - Midlothian TX: 1.08, 1.12
  - Henderson NV: 1.08, 1.10
  - Storey County NV (air-cooled): 1.11, 1.17
  - Red Oak TX: 1.10, 1.14 (cooling type not stated)
  - Fleet: Q2 quarterly 1.10, TTM 1.09; 2025 annual 1.09.
- **[D] comparisons:**
  - Storey County (air-cooled; Reno-area high desert, *cooler* than Henderson) runs about **+0.07 PUE** above Henderson (evaporative, Las Vegas area): 2024 annual 1.16 vs 1.09, Q2 2026 1.17 vs 1.10.
  - Mesa (air-cooled, ramping up) runs about **+0.14 to +0.16** above Midlothian TX in Q1-Q2 2026.
  - Dublin, air-cooled in a mild maritime climate, reaches 1.08.
  - Caveats: vintage, load and IT mix differ across sites. Ramp-up partial load inflates the PUE of new sites such as Mesa.
- **Quote [V]** (ER 2025, p. 69): air cooling "doesn't consume water for cooling during routine operations".
- **Google overall:**
  - Annual air-cooled penalty of roughly +0.07 PUE in a dry climate. That is a ~6-7% total-energy increase, consistent with the "about 10%" claim.
  - Larger penalties in hot desert sites and on peak days.

## 5. Meta

- **Citation:** Meta (Oct 2025). *2025 Environmental Data Index.* https://sustainability.atmeta.com/wp-content/uploads/2025/10/Meta_2025-Environmental-Data-Index.pdf (asset page: https://sustainability.atmeta.com/asset/2025-environmental-data-index)
- **Type:** company disclosure.
- **Numbers [V]:**
  - Fleet PUE: 1.10 (2020), 1.09, 1.08, 1.08, **1.08 (2024)**.
  - Fleet WUE: 0.30, 0.26, 0.20, 0.18, **0.19 L/kWh (2024)**.
  - Meta's WUE is **withdrawal** divided by IT kWh (definitions page, near the end of the index): "Annual WUE is calculated by dividing our water withdrawal, in liters, by IT electricity load".
  - **Per-site PUE and WUE are not published.** The index gives per-site electricity (MWh) and water withdrawal (megaliters) only.
- **[D] Per-site withdrawal per total facility kWh, 2024:**

| Site | L/kWh |
|---|---|
| Fort Worth TX | 0.28 |
| Los Lunas NM | 0.22 |
| Prineville OR | 0.19 |
| New Albany OH | 0.17 |
| Altoona IA | 0.15 |
| Eagle Mountain UT | 0.12 |
| Henrico VA | 0.10 |
| DeKalb IL (ramping) | 0.28 |
| Mesa AZ (first year) | 2.3 |
| Owned fleet | about 0.22 |

  - These do not reproduce the published 0.19 exactly. The basis may exclude some water or facilities.
- **Dry vs evaporative:** No direct evidence. Meta runs direct evaporative cooling with low PUE (1.08) and low withdrawal-based WUE (~0.1-0.3). This is the "airside + adiabatic" archetype, and the high-PUE/low-water trade-off does not apply to it.

## 6. Amazon / AWS

### 6a. Amazon water-efficiency article
- **Citation:** Amazon (Jun 11, 2026). "How Amazon is making its data centers more water-efficient." https://aboutamazon.com/news/sustainability/amazon-data-center-water-usage
- **Type:** company disclosure.
- **Quotes [V]:**
  - On free-air cooling: "About 90% of the time" (no water).
  - Water is used only when ambient temperature exceeds "roughly 85° F".
  - "chillers typically require 25% to 35% more electricity". The clause continues that this extra demand coincides with peak grid load.
  - The baseline is not stated. In context it means chillers vs Amazon's direct evaporative mode on the hottest days. Whether the base is facility or cooling electricity is unclear.
- **Numbers [V]:** 0.12 L/kWh in 2025 (withdrawal per IT kWh); 0.25 in 2021.

### 6b. AWS cloud sustainability page
- **URL:** https://sustainability.aboutamazon.com/products-services/aws-cloud
- **Numbers [V]:** Global PUE 1.14 (2025), 1.15 (2024). Global WUE 0.12 L/kWh withdrawn per IT kWh (2025).
- **Quote [V]:** AWS "seeks the optimal balance of energy and water use."
- The global WUE for 2024 (0.15) was not confirmed on this page.

### 6c. AWS regional fact sheets
- **URL pattern:** https://sustainability.aboutamazon.com/aws-sustainability-fact-sheets/aws-fact-sheet-<state>.pdf
- **Values [V], PUE 2023 / 2024 / 2025 and WUE 2024 / 2025:**

| Region | PUE 2023 | PUE 2024 | PUE 2025 | WUE 2024 | WUE 2025 |
|---|---|---|---|---|---|
| US East, Northern Virginia | 1.15 | 1.15 | 1.15 | 0.12 | 0.06 |
| US East, Ohio | 1.12 | 1.13 | 1.12 | 0.10 | 0.06 |
| US West, Oregon | 1.13 | 1.12 | 1.12 | 0.16 | 0.12 |
| US West, Northern California | 1.17 | 1.18 | 1.18 | 0.51 | 0.39 |

  - Ohio's 2022 PUE was 1.12.

### 6d. AWS Australia
- **Citation:** O'Rourke, M. (Jun 25, 2026). AWS Australia. https://www.aboutamazon.com.au/news/aws/how-amazon-uses-water-to-keep-australias-digital-economy-running
- **Quote [V]:** "Amazon uses no water to cool its data centres for 95.5 per cent of the year."
- **AWS overall:** On the hottest days, chillers would take 25-35% more electricity than evaporative cooling. This is the clearest operator statement on the **peak** penalty. The annual penalty is not given.

## 7. Uptime Institute

### 7a. Global Data Center Survey 2025
- **Citation:** Uptime Institute (Jul 2025). *Uptime Institute Global Data Center Survey 2025* (Keynote Report 180). https://datacenter.uptimeinstitute.com/rs/711-RIA-145/images/2025.Annual.Survey.Report.pdf
- **Type:** trade survey.
- **Numbers [V]** (Figure 2, p. 7): weighted average annual PUE was **1.56 in 2024 and 1.54 in 2025** (n=681). Earlier: 1.55 (2022), 1.58 (2023).
- **Other values [V]:** Facilities built since about 2020 average 1.48. Sites of 20 MW or more average 1.44.
- **Quote [V]:** "the most energy-efficient heat rejection systems will remain untenable in some regions."

### 7b. Briefing Report 156
- **Citation:** Dietrich, J. (Oct 24, 2024). "Cooling systems: balancing cost, energy and water use." UII Briefing Report 156. https://intelligence.uptimeinstitute.com/resource/cooling-systems-balancing-cost-energy-and-water-use
- **Quote [V]** (summary only; the rest is paywalled): "Both air-cooled and water-cooled systems offer full economization, low PUEs and comparable total cost of ownership".

### 7c. Briefing Report 200
- **Citation:** Talib, R., Dietrich, J. (Apr 24, 2026). "Dry cooling energy performance can rival evaporative cooling." UII Briefing Report 200. https://intelligence.uptimeinstitute.com/resource/dry-cooling-energy-performance-can-rival-evaporative-cooling
- **Basis:** Operating PUE and WUE data from sites across ASHRAE zones.
- **Quote [V]** (summary): "Well-designed dry cooling and adiabatic systems can match evaporative cooling PUE across ASHRAE climate zones 2-6".
- **Numbers are paywalled.**

### 7d. Client webinar 007
- **Citation:** Talib and Dietrich (Jun 24, 2026), UII Client Webinar 007. https://intelligence.uptimeinstitute.com/resource/replay-uptime-intelligence-client-webinar-view-efficiency-through-pue-and-wue
- **Content [V]:** Monthly PUE and WUE from operational data. Both system types "can achieve efficient PUE and WUE values". Numbers are paywalled.

- **Not reachable:** I found no Rahkonen or Bizo note on dry-cooling peak penalty. The Uptime Cooling Systems Survey 2024 and Field Report 181 PDF returned 404.
- **Uptime overall:** Its recent work argues that the dry-cooling annual penalty can be near zero with good design and operations. It is the most favorable source for dry cooling.

## 8. Other operators, applicants and studies

- **Crusoe, Abilene TX (Stargate phase 1)**
  - **Citation:** Crusoe, "Crusoe's 2025 Impact Report" (blog, May 28, 2026), https://www.crusoe.ai/resources/blog/crusoes-2025-impact-report, and "An inside look at the Abilene AI data center" (Aug 5, 2025), https://www.crusoe.ai/blog/an-inside-look-at-the-abilene-ai-data-center
  - **Type:** company disclosure.
  - **Quotes [V]:**
    - "closed-loop, non-evaporative liquid cooling systems", with heat rejected through "air-cooled chillers".
    - "built to an annualized design Power Usage Effectiveness (PUE) of 1.2 to 1.4".
    - The 2026 target for new projects is "1.1 to 1.25".
  - **Water:** 1 million gal initial fill per building, ~50,000 gal per building per year.
  - **Note:** This is the closest real analogue to the model's dry case in a hot Texas climate (Abilene is 3B). Its design PUE of 1.2-1.4 brackets the model's Dallas dry values: 1.233 on the shared loop, 1.351 with chilled water.
- **Project Blue, Tucson / Pima County AZ (Beale Infrastructure)**
  - **Source:** Boulard, G. (Dec 9, 2025), Construction Reporter, https://constructionreporter.com/giant-project-blue-project-in-arizona-moving-forward-but-perhaps-without-amazon-as-a-client/. Type: press.
  - **Content [V]:** Beale switched to "air cooling technology that would utilize a closed-loop system". TEP would serve "upwards of 350 megawatts".
  - The City of Tucson cites 400-600 MW at buildout [S, KGUN].
  - **No PUE stated** in any source I found.
- **Google, Botetourt County VA**
  - **Source:** Simone, J. (Jul 23-24, 2026), WSET. https://wset.com/newsletter-daily/at-greenfield-industrial-park-google-revises-cooling-plan-for-first-botetourt-data-center-july-2026. Type: press.
  - **Content [V]:** The first building switched from water to air cooling. No PUE or power figure.
- **Aligned Data Centers, "Protecting Regional Water Resources" case study** (2025)
  - **URL:** https://aligneddc.com/wp-content/uploads/2025/10/Aligned-Water-Savings-Case-Study.pdf
  - **Content [V]:** Delta3 air cooling and DeltaFlow liquid cooling are closed-loop with "waterless heat rejection".
  - **No PUE number.**
- **STACK Infrastructure**
  - **Citation:** Medina, B. (Feb 2, 2021), "The Case for Air-Cooled Data Centers." https://stackinfra.com/resources/blog/the-case-for-air-cooled-data-centers
  - **Quote [V]:** "water-cooled systems may be more efficient than air-cooled systems on the whole". No numbers.
- **Herbert, M. (May 9, 2020)**, "Air-cooled chillers are back in data centers," ACHR News. https://www.achrnews.com/articles/160624-air-cooled-chillers-are-back-in-data-centers-and-they-mean-business
  - **Type:** trade press by a P.E.
  - **Numbers [V]:** Economizing air-cooled chillers with 55-65 F chilled water reach "annualized pPUE values in the 1.18-1.2 range". This is cooling partial PUE only.
- **SemiAnalysis**
  - **Citation:** Ontiveros, J.E. et al. (Feb 13, 2025), "Datacenter Anatomy Part 2 – Cooling Systems." https://newsletter.semianalysis.com/p/datacenter-anatomy-part-2-cooling-systems
  - **Type:** trade analysis; mostly paywalled.
  - **Numbers [V], visible part:**
    - The largest air-cooled chiller SKU cools 2 MW and draws 500 kW (COP ~4 at 35 C ambient with 20/30 C water).
    - Water-cooled chiller COP is "around 7x".
  - **Note:** This is a peak-condition chiller ratio, not PUE.
- **Alston, Love, Haider (Sep 21, 2026)**, "Data Center Cooling Choices Shift Water Impacts Across the Grid." arXiv:2609.25437, University of Michigan. https://arxiv.org/abs/2609.25437
  - **Type:** preprint, not peer-reviewed. **Michigan case.**
  - **Numbers [V], Table 2:** For a 200 MW IT load, an air-cooled chiller uses 4.06 TWh vs 3.08 TWh for a water-cooled chiller, **+32%**.
  - **[D] Implied PUE:** 2.32 vs 1.76.
  - **Caveat [V]:** The PUEs are "selected from the upper endpoints of their respective midsize data center performance ranges" in LBNL 2024, "representing worst-case configurations".
  - **Warning:** If this paper is cited against Water Ledger, its 32% is a worst-case midsize figure, not a hyperscale one.
- **Koomey, J. (Aug 17, 2026)**, blog review of fleet PUE/WUE for the top 20 operators. https://www.koomey.com/koomey_blog/reviewing-fleet-average-onsite-water-and-infrastructure-energy-efficiency-for-the-top-twenty-global-data-center-operators/
  - **Quote [V]:** "onsite water use can often lead to lower PUEs". It notes Meta has the lowest combined PUE+WUE.
  - The numbers are in an image I did not extract.
- **Not covered:** No usable PUE was found for xAI Memphis or for Equinix, Digital Realty, Vantage, CyrusOne or QTS statements on the water-free energy cost.
- **Additional peer-reviewed source, not requested:** Chen, L., Wemhoff, A.P. (2023), *RCR* 196:107053. It models a 400 kW chilled-water CRAH data center at 925 US sites (https://par.nsf.gov/servlets/purl/10435467). Economization cuts state-mean PUE by 11%. It has no dry vs tower comparison.

---

## Summary against the model

**Annual penalty, warm-water or economized large sites**

| Source | Dry penalty, annual dPUE |
|---|---|
| LBNL 2024, large-scale air IT [F] | +0.03 to +0.08 |
| LBNL 2024, liquid IT (W45) [F] | about 0 or slightly negative |
| Google, Storey County vs Henderson [D] | about +0.07 |
| Google, "about 10% less energy" for water cooling [V] | about +0.1 at PUE 1.1, if the base is total energy |
| Microsoft [V] | "nominal" (no number) |
| Uptime 2026 [V] | can match in zones 2-6 |

- **Model:** +0.038 (Michigan), +0.042 (Virginia), +0.057 (Dallas). These sit in the middle of this evidence: below Google's "10%" and the Storey/Henderson gap, and above Uptime's "can match" and LBNL's liquid-cooled case.

**Climate gradient**
- Lei and Masanet midsize air-cooled vs water-cooled chiller [F]: 5A ~+0.06, 4A ~+0.10, 3A ~+0.15, 2B ~+0.33.
- This has the same ordering as the model (MI < VA < TX), with a steeper slope at midsize and with no economizer.

**Chilled water (7-13 C), Dallas**
- Model: 1.351 vs 1.268 (+0.083).
- Lei and Masanet 3A midsize with no economizer: about +0.15.
- Crusoe Abilene air-cooled chiller design: 1.2-1.4.
- So the model is plausible and perhaps on the low side for the gap.

**Peak**
- Amazon: chillers need 25-35% more electricity than evaporative cooling on the hottest days [V].
- Google via Latitude: air cooling up to 50% more energy on peak days than on an average day [V, ambiguous base].
- SemiAnalysis: chiller COP ~4 (air-cooled, 35 C) vs ~7 (water-cooled) [V].
- No source gives a peak PUE by cooling type.
