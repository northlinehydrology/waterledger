# Michigan on the base: every difference from the before record

Design 0011 step 6, Nov 25, 2026 (rerun after a place's water systems were limited to those on 5% of it or more): every field that differs between Michigan's answers on its former path (3.27.0, snapshot 2026-11-17; `tests/data/michigan_before_0011.json.xz`) and on the base with its layers (a local snapshot built Nov 25), by `tests/michigan_after_0011.py`. The causes are in the note, section "Step 6, the after record".

11,112 cases at 1,541 places; 240,658 differing values in 276 fields.

| Part | Field | Places | Values | Largest relative change | Example (place, before → after) |
|---|---|---|---|---|---|
| context | `/ok/climate/provider` | 1,541 | 1,541 | | 2600101040 context: "MI" → "national" |
| context | `/ok/climate/sources` | 1,541 | 1,541 | | 2600101040 context: ["era5", "noaa_cag", "noaa_atlas14"] → ["noaa_isd", "noaa_cag", "noaa_atlas14", "era5"] |
| context | `/ok/energy/provider` | 1,541 | 1,541 | | 2600101040 context: "MI" → "national" |
| context | `/ok/energy/sources[]` | 1,541 | 4,623 | | 2600101040 context: "eia923_2024" → "siddik2024" |
| context | `/ok/jurisdiction/provider` | 1,541 | 1,541 | | 2600101040 context: "MI" → "national" |
| context | `/ok/receiving/provider` | 1,541 | 1,541 | | 2600101040 context: "MI" → "national" |
| context | `/ok/supply/county_use_mgd/total` | 1,541 | 1,541 | | 2600101040 context: "<absent>" → 0.261 |
| context | `/ok/supply/provider` | 1,541 | 1,541 | | 2600101040 context: "MI" → "national" |
| context | `/ok/supply/sources[]` | 1,541 | 3,082 | | 2600101040 context: "wellogic" → "usgs_wu2015" |
| context | `/ok/wastewater/provider` | 1,541 | 1,541 | | 2600101040 context: "MI" → "national" |
| context | `/ok/wastewater/sources[]` | 1,541 | 3,082 | | 2600101040 context: "echo" → "cwns2022" |
| estimate | `/ok/data_date` | 1,541 | 6,489 | | 2600101040 assist: "2026-11-17" → "2026-11-25" |
| estimate | `/ok/power_plants/miso/returned` | 1,541 | 6,489 | 0.0422 | 2600101040 assist: 84.02796970885178 → 80.56142203248933 |
| estimate | `/ok/power_plants/miso/withdrawn/p10` | 1,541 | 6,489 | 0.0408 | 2600101040 assist: 70.24806073354164 → 67.42975325716282 |
| estimate | `/ok/power_plants/miso/withdrawn/p50` | 1,541 | 6,489 | 0.041 | 2600101040 assist: 86.40584951991032 → 82.93930184354787 |
| estimate | `/ok/power_plants/miso/withdrawn/p90` | 1,541 | 6,489 | 0.0411 | 2600101040 assist: 101.91411803225124 → 97.82538849581145 |
| estimate | `/ok/power_plants/pjm` | 1,541 | 6,489 | | 2600101040 assist: "<absent>" → {"option": "pjm", "label": "PJM grid average", "consumed": { |
| estimate | `/ok/power_plants/state_mix/sources` | 1,541 | 6,489 | | 2600101040 assist: ["eia923_2024", "eia_mi", "macknick2012"] → ["eia923_2024", "eia_sep2024", "macknick2012", "siddik2024"] |
| reference | `/ok/golf_note` | 1,541 | 1,541 | | 2600101040 reference: "The median of Michigan courses reporting to EGLE. Only faci → "This is the median of Michigan courses reporting to EGLE fo |
| reference | `/ok/not_covered` | 1,541 | 1,541 | | 2600101040 reference: "<absent>" → {} |
| reference | `/ok/power_options/miso/note` | 1,541 | 1,541 | | 2600101040 reference: "1.57 L/kWh consumed and 57.1 L/kWh withdrawn, MISO excludin → "1.57 L/kWh consumed and 55 withdrawn, MISO excluding hydrop |
| reference | `/ok/power_options/miso/wd_gal_mwh` | 1,541 | 1,541 | 0.0401 | 2600101040 reference: 15080 → 14475 |
| reference | `/ok/power_options/miso/wd_hi` | 1,541 | 1,541 | 0.0401 | 2600101040 reference: 15080 → 14475 |
| reference | `/ok/power_options/miso/wd_lo` | 1,541 | 1,541 | 0.0401 | 2600101040 reference: 15080 → 14475 |
| reference | `/ok/power_options/pjm` | 1,541 | 1,541 | | 2600101040 reference: "<absent>" → {"label": "PJM grid average", "gal_mwh": 343, "lo": 343, "hi |
| reference | `/ok/power_options/state_mix/note` | 1,541 | 1,541 | | 2600101040 reference: "1.01 L/kWh consumed (0.74 to 1.38) and 59 L/kWh withdrawn ( → "1.01 L/kWh consumed (0.74 to 1.38) and 59 withdrawn (38 to  |
| reference | `/ok/power_options/state_mix/sources` | 1,541 | 1,541 | | 2600101040 reference: ["eia923_2024", "eia_mi", "macknick2012"] → ["eia923_2024", "eia_sep2024", "macknick2012", "siddik2024"] |
| reference | `/ok/state_avg_mw` | 1,541 | 1,541 | 9.32e-06 | 2600101040 reference: 11468 → 11468.106849315069 |
| context | `/ok/energy/utilities[]/avg_mw` | 1,537 | 2,192 | 98.1 | 2600101040 context: 4271.9 → 4271.883219178082 |
| estimate | `/ok/comparisons[]/existing` | 1,527 | 15,477 | 98.1 | 2600101040 assist: 4271.9 → 4271.883219178082 |
| estimate | `/ok/comparisons[]/percent/avg/p10` | 1,527 | 15,503 | 98.1 | 2600101040 assist: 4.316425840799294 → 4.316442796593645 |
| estimate | `/ok/comparisons[]/percent/avg/p50` | 1,527 | 15,503 | 98.1 | 2600101040 assist: 5.309248935406912 → 5.309269791211327 |
| estimate | `/ok/comparisons[]/percent/avg/p90` | 1,527 | 15,503 | 98.1 | 2600101040 assist: 6.262161944730173 → 6.262186543769759 |
| context | `/ok/supply/county_use_mgd/Public water systems` | 1,522 | 1,522 | | 2600101040 context: 0.05 → "<absent>" |
| context | `/ok/supply/county_use_mgd/public_supply` | 1,522 | 1,522 | | 2600101040 context: "<absent>" → 0.05 |
| context | `/ok/supply/county_use_mgd/Golf courses` | 1,519 | 1,519 | | 2600101040 context: 0.088 → "<absent>" |
| context | `/ok/supply/county_use_mgd/golf` | 1,519 | 1,519 | | 2600101040 context: "<absent>" → 0.088 |
| context | `/ok/wastewater/plants[]/km` | 1,486 | 8,619 | 1.99 | 2600101040 context: 28.20846061279605 → 28.24250896903584 |
| context | `/ok/place/lon` | 1,474 | 1,474 | 1.45e-05 | 2600101040 context: -83.4478 → -83.4486 |
| estimate | `/ok/site/place/lon` | 1,474 | 6,212 | 1.45e-05 | 2600101040 assist: -83.4478 → -83.4486 |
| place | `/ok/lon` | 1,474 | 1,474 | 1.45e-05 | 2600101040 place: -83.4478 → -83.4486 |
| context | `/ok/supply/county_use_mgd/Farm irrigation` | 1,459 | 1,459 | | 2600101040 context: 0.029 → "<absent>" |
| context | `/ok/supply/county_use_mgd/irrigation` | 1,459 | 1,459 | | 2600101040 context: "<absent>" → 0.029 |
| context | `/ok/place/lat` | 1,453 | 1,453 | 1.92e-05 | 2600101040 context: 44.8067 → 44.8071 |
| estimate | `/ok/site/place/lat` | 1,453 | 6,120 | 1.92e-05 | 2600101040 assist: 44.8067 → 44.8071 |
| place | `/ok/lat` | 1,453 | 1,453 | 1.92e-05 | 2600101040 place: 44.8067 → 44.8071 |
| context | `/ok/climate/cell_km` | 1,436 | 1,436 | 0.321 | 2600112460 context: 12.32 → 12.33 |
| context | `/ok/supply/county_use_mgd/Industry` | 1,388 | 1,388 | | 2600304460 context: 3.423 → "<absent>" |
| context | `/ok/supply/county_use_mgd/industrial` | 1,388 | 1,388 | | 2600304460 context: "<absent>" → 3.423 |
| context | `/ok/supply/county_use_mgd/Mining and dewatering` | 1,208 | 1,208 | | 2600101040 context: 0.094 → "<absent>" |
| context | `/ok/supply/county_use_mgd/mining` | 1,208 | 1,208 | | 2600101040 context: "<absent>" → 0.094 |
| context | `/ok/receiving/watersheds` | 900 | 900 | | 2600101040 context: [{"huc12": "040700030404", "name": "North Branch Black River → [{"huc12": "040700030404", "name": "North Branch Black River |
| context | `/ok/supply/county_use_mgd/Other` | 866 | 866 | | 2600501260 context: 2.057 → "<absent>" |
| context | `/ok/supply/county_use_mgd/other` | 866 | 866 | | 2600501260 context: "<absent>" → 2.057 |
| context | `/ok/receiving/watersheds[]/share_of_place` | 572 | 1,817 | 0.367 | 2600136860 context: 0.78 → 0.794 |
| context | `/ok/supply/county_use_mgd/Power plants` | 536 | 536 | | 2600101040 context: 0.0 → "<absent>" |
| context | `/ok/supply/county_use_mgd/thermoelectric` | 536 | 536 | | 2600101040 context: "<absent>" → 0.0 |
| context | `/ok/supply/county_use_mgd/Livestock` | 522 | 522 | | 2600501260 context: 1.699 → "<absent>" |
| context | `/ok/supply/county_use_mgd/livestock` | 522 | 522 | | 2600501260 context: "<absent>" → 1.699 |
| context | `/ok/supply/systems[]/share_of_place` | 436 | 499 | 0.807 | 2600136860 context: 0.82 → 0.894 |
| estimate | `/ok/before_after[]/after` | 364 | 1,438 | 0.253 | 2600101040 lake: 147.30561 → 147.30559883989235 |
| estimate | `/ok/before_after[]/after_high` | 352 | 1,365 | 0.313 | 2600101040 lake: 194.04045 → 194.04043681080043 |
| estimate | `/ok/before_after[]/after_low` | 352 | 1,366 | 0.218 | 2600101040 lake: 112.5096 → 112.50960552875644 |
| estimate | `/ok/electricity/avg_mw/p10` | 328 | 337 | 0.00073 | 2600101040 lake: 176.87025 → 176.87024414876268 |
| estimate | `/ok/electricity/avg_mw/p50` | 328 | 337 | 0.000947 | 2600101040 lake: 217.40703 → 217.40703039017902 |
| estimate | `/ok/electricity/avg_mw/p90` | 328 | 337 | 0.00106 | 2600101040 lake: 256.04586 → 256.0458530173711 |
| estimate | `/ok/electricity/peak_mw/p10` | 328 | 337 | 0.00091 | 2600101040 lake: 318.6477 → 318.6476976122983 |
| estimate | `/ok/electricity/peak_mw/p50` | 328 | 337 | 0.000912 | 2600101040 lake: 333.00678000000005 → 333.00677037347504 |
| estimate | `/ok/electricity/peak_mw/p90` | 328 | 337 | 0.00101 | 2600101040 lake: 347.39526 → 347.39526351759014 |
| estimate | `/ok/electricity/peak_pue/p10` | 328 | 337 | 0.00091 | 2600101040 lake: 1.06216 → 1.0621589920409946 |
| estimate | `/ok/electricity/peak_pue/p50` | 328 | 337 | 0.000912 | 2600101040 lake: 1.11002 → 1.1100225679115834 |
| estimate | `/ok/electricity/peak_pue/p90` | 328 | 337 | 0.00101 | 2600101040 lake: 1.15798 → 1.1579842117253005 |
| estimate | `/ok/electricity/pue/p10` | 328 | 337 | 0.000939 | 2600101040 lake: 1.06216 → 1.0621589920409946 |
| estimate | `/ok/electricity/pue/p50` | 328 | 337 | 0.00102 | 2600101040 lake: 1.11002 → 1.1100225679115834 |
| estimate | `/ok/electricity/pue/p90` | 328 | 337 | 0.00115 | 2600101040 lake: 1.15798 → 1.1579842117253005 |
| estimate | `/ok/equivalents/electricity_homes/p10` | 328 | 337 | 0.00073 | 2600101040 lake: 203363.17924082532 → 203363.1725131466 |
| estimate | `/ok/equivalents/electricity_homes/p50` | 328 | 337 | 0.000947 | 2600101040 lake: 249971.8568278469 → 249971.85727646982 |
| estimate | `/ok/equivalents/electricity_homes/p90` | 328 | 337 | 0.00106 | 2600101040 lake: 294398.2954796031 → 294398.28745106456 |
| estimate | `/ok/equivalents/electricity_homes_peak/p10` | 328 | 337 | 0.00091 | 2600101040 lake: 366377.10033076076 → 366377.0975854115 |
| estimate | `/ok/equivalents/electricity_homes_peak/p50` | 328 | 337 | 0.000912 | 2600101040 lake: 382886.9891321468 → 382886.97806369 |
| estimate | `/ok/equivalents/electricity_homes_peak/p90` | 328 | 337 | 0.00101 | 2600101040 lake: 399430.6816821547 → 399430.6857266354 |
| estimate | `/ok/equivalents/evaporated_share` | 328 | 337 | 0.0315 | 2600101040 lake: 0.580609251745402 → 0.5806161643256627 |
| estimate | `/ok/equivalents/golf_courses/p10` | 328 | 337 | 0.102 | 2600101040 lake: 15.458620689655172 → 15.458691419656075 |
| estimate | `/ok/equivalents/golf_courses/p50` | 328 | 337 | 0.0757 | 2600101040 lake: 19.661379310344827 → 19.66161190393404 |
| estimate | `/ok/equivalents/golf_courses/p90` | 328 | 337 | 0.0653 | 2600101040 lake: 25.886206896551723 → 25.886492692237162 |
| estimate | `/ok/equivalents/homes/p10` | 328 | 337 | 0.102 | 2600101040 lake: 3886.9711374769677 → 3886.988922082566 |
| estimate | `/ok/equivalents/homes/p50` | 328 | 337 | 0.0757 | 2600101040 lake: 4943.727867871107 → 4943.786352039015 |
| estimate | `/ok/equivalents/homes/p90` | 328 | 337 | 0.0653 | 2600101040 lake: 6508.920885353467 → 6508.992746847634 |
| estimate | `/ok/equivalents/homes_peak_day/p10` | 328 | 337 | 0.0679 | 2600101040 lake: 5188.235086423082 → 5188.293382077547 |
| estimate | `/ok/equivalents/homes_peak_day/p50` | 328 | 337 | 0.0584 | 2600101040 lake: 6573.255763426363 → 6573.304331222915 |
| estimate | `/ok/equivalents/homes_peak_day/p90` | 328 | 337 | 0.0622 | 2600101040 lake: 8618.099111770258 → 8618.026107103296 |
| estimate | `/ok/equivalents/share_of_home_customers/p10` | 328 | 337 | 0.00073 | 2600101040 lake: 4.481284039703902 → 4.481283891453666 |
| estimate | `/ok/equivalents/share_of_home_customers/p50` | 328 | 337 | 0.000947 | 2600101040 lake: 5.50834667593011 → 5.508346685815905 |
| estimate | `/ok/equivalents/share_of_home_customers/p90` | 328 | 337 | 0.00106 | 2600101040 lake: 6.48732178447342 → 6.487321607557609 |
| estimate | `/ok/power_plants/coal/consumed/p10` | 328 | 337 | 0.00073 | 2600101040 lake: 0.4468301052631579 → 0.44683009048108474 |
| estimate | `/ok/power_plants/coal/consumed/p50` | 328 | 337 | 0.000947 | 2600101040 lake: 1.3730970315789475 → 1.373097034043236 |
| estimate | `/ok/power_plants/coal/consumed/p90` | 328 | 337 | 0.00106 | 2600101040 lake: 2.050523055663158 → 2.0505229997433254 |
| estimate | `/ok/power_plants/coal/returned` | 328 | 337 | 0.000947 | 2600101040 lake: 198.27521136000004 → 198.27521171584328 |
| estimate | `/ok/power_plants/coal/withdrawn/p10` | 328 | 337 | 0.00073 | 2600101040 lake: 89.36602105263158 → 89.36601809621695 |
| estimate | `/ok/power_plants/coal/withdrawn/p50` | 328 | 337 | 0.000947 | 2600101040 lake: 199.64830839157898 → 199.64830874988652 |
| estimate | `/ok/power_plants/coal/withdrawn/p90` | 328 | 337 | 0.00106 | 2600101040 lake: 323.42634947368424 → 323.42634065352144 |
| estimate | `/ok/power_plants/coal/withdrawn_fresh` | 328 | 337 | 0.000947 | 2600101040 lake: 199.64830839157898 → 199.64830874988652 |
| estimate | `/ok/power_plants/miso/consumed/p10` | 328 | 337 | 0.00073 | 2600101040 lake: 1.8543449368421054 → 1.8543448754965015 |
| estimate | `/ok/power_plants/miso/consumed/p50` | 328 | 337 | 0.000947 | 2600101040 lake: 2.2793410724210528 → 2.279341076511771 |
| estimate | `/ok/power_plants/miso/consumed/p90` | 328 | 337 | 0.00106 | 2600101040 lake: 2.6844387006315795 → 2.6844386274242273 |
| estimate | `/ok/power_plants/new_gas/consumed/p10` | 328 | 337 | 0.00073 | 2600101040 lake: 0.5808791368421053 → 0.5808791176254101 |
| estimate | `/ok/power_plants/new_gas/consumed/p50` | 328 | 337 | 0.000947 | 2600101040 lake: 1.1259395658947369 → 1.1259395679154534 |
| estimate | `/ok/power_plants/new_gas/consumed/p90` | 328 | 337 | 0.00106 | 2600101040 lake: 1.9405580968421055 → 1.9405580439211283 |
| estimate | `/ok/power_plants/new_gas/returned` | 328 | 337 | 0.000947 | 2600101040 lake: 0.2746194063157896 → 0.2746194068086474 |
| estimate | `/ok/power_plants/new_gas/withdrawn/p10` | 328 | 337 | 0.00073 | 2600101040 lake: 0.6702451578947368 → 0.670245135721627 |
| estimate | `/ok/power_plants/new_gas/withdrawn/p50` | 328 | 337 | 0.000947 | 2600101040 lake: 1.4005589722105265 → 1.4005589747241007 |
| estimate | `/ok/power_plants/new_gas/withdrawn/p90` | 328 | 337 | 0.00106 | 2600101040 lake: 1.8305931380210527 → 1.8305930880989312 |
| estimate | `/ok/power_plants/nuclear/consumed/p10` | 328 | 337 | 0.00073 | 2600101040 lake: 1.1215435642105265 → 1.1215435271075227 |
| estimate | `/ok/power_plants/nuclear/consumed/p50` | 328 | 337 | 0.000947 | 2600101040 lake: 2.174985698021053 → 2.1749857019244856 |
| estimate | `/ok/power_plants/nuclear/consumed/p90` | 328 | 337 | 0.00106 | 2600101040 lake: 3.4930045743157896 → 3.493004479058031 |
| estimate | `/ok/power_plants/nuclear/returned` | 328 | 337 | 0.000947 | 2600101040 lake: 166.79284261995792 → 166.79284291929994 |
| estimate | `/ok/power_plants/nuclear/withdrawn/p10` | 328 | 337 | 0.00073 | 2600101040 lake: 77.73950171368422 → 77.7394991418991 |
| estimate | `/ok/power_plants/nuclear/withdrawn/p50` | 328 | 337 | 0.000947 | 2600101040 lake: 168.96782831797898 → 168.96782862122444 |
| estimate | `/ok/power_plants/nuclear/withdrawn/p90` | 328 | 337 | 0.00106 | 2600101040 lake: 271.4711406942316 → 271.47113329093975 |
| estimate | `/ok/power_plants/nuclear/withdrawn_fresh` | 328 | 337 | 0.000947 | 2600101040 lake: 168.96782831797898 → 168.96782862122444 |
| estimate | `/ok/power_plants/renew/consumed/p50` | 328 | 337 | 0.000947 | 2600101040 lake: 0.0008787821002105264 → 0.000878782101787671 |
| estimate | `/ok/power_plants/renew/consumed/p90` | 328 | 337 | 0.00106 | 2600101040 lake: 0.005110136321684211 → 0.0051101361823256385 |
| estimate | `/ok/power_plants/renew/withdrawn/p50` | 328 | 337 | 0.000947 | 2600101040 lake: 0.0008787821002105264 → 0.000878782101787671 |
| estimate | `/ok/power_plants/renew/withdrawn/p90` | 328 | 337 | 0.00106 | 2600101040 lake: 0.005110136321684211 → 0.0051101361823256385 |
| estimate | `/ok/power_plants/state_mix/consumed/p10` | 328 | 337 | 0.00073 | 2600101040 lake: 0.8757870063157895 → 0.875786977342926 |
| estimate | `/ok/power_plants/state_mix/consumed/p50` | 328 | 337 | 0.000947 | 2600101040 lake: 1.4719600178526315 → 1.4719600204943488 |
| estimate | `/ok/power_plants/state_mix/consumed/p90` | 328 | 337 | 0.00106 | 2600101040 lake: 2.354543824168421 → 2.354543759957636 |
| estimate | `/ok/power_plants/state_mix/returned` | 328 | 337 | 0.000947 | 2600101040 lake: 83.52823862501053 → 83.52823877491814 |
| estimate | `/ok/power_plants/state_mix/withdrawn/p10` | 328 | 337 | 0.00073 | 2600101040 lake: 45.219206652631584 → 45.21920515668577 |
| estimate | `/ok/power_plants/state_mix/withdrawn/p50` | 328 | 337 | 0.000947 | 2600101040 lake: 85.00019864286317 → 85.00019879541249 |
| estimate | `/ok/power_plants/state_mix/withdrawn/p90` | 328 | 337 | 0.00106 | 2600101040 lake: 153.09062825987368 → 153.09062408493782 |
| estimate | `/ok/power_plants/state_mix/withdrawn_fresh` | 328 | 337 | 0.000947 | 2600101040 lake: 85.00019864286317 → 85.00019879541249 |
| estimate | `/ok/water/consumed/avg/p10` | 328 | 337 | 0.165 | 2600101040 lake: 0.67245 → 0.6724530767550393 |
| estimate | `/ok/water/consumed/avg/p50` | 328 | 337 | 0.105 | 2600101040 lake: 0.85527 → 0.8552801178211308 |
| estimate | `/ok/water/consumed/avg/p90` | 328 | 337 | 0.0843 | 2600101040 lake: 1.12605 → 1.1260624321123167 |
| estimate | `/ok/water/consumed/peak_day/p10` | 328 | 337 | 0.0752 | 2600101040 lake: 0.89757 → 0.8975800852081115 |
| estimate | `/ok/water/consumed/peak_day/p50` | 328 | 337 | 0.0609 | 2600101040 lake: 1.13718 → 1.1371884022786987 |
| estimate | `/ok/water/consumed/peak_day/p90` | 328 | 337 | 0.0543 | 2600101040 lake: 1.49094 → 1.4909273701176156 |
| estimate | `/ok/water/consumed_max_90day/p10` | 328 | 337 | 0.0661 | 2600101040 lake: 0.89757 → 0.8975800852081115 |
| estimate | `/ok/water/consumed_max_90day/p50` | 328 | 337 | 0.0588 | 2600101040 lake: 1.13718 → 1.1371884022786987 |
| estimate | `/ok/water/consumed_max_90day/p90` | 328 | 337 | 0.05 | 2600101040 lake: 1.49094 → 1.4909273701176156 |
| estimate | `/ok/water/returned/avg/p10` | 328 | 337 | 0.041 | 2600101040 lake: 112.5096 → 112.50960552875644 |
| estimate | `/ok/water/returned/avg/p50` | 328 | 337 | 0.0365 | 2600101040 lake: 147.30561 → 147.30559883989235 |
| estimate | `/ok/water/returned/avg/p90` | 328 | 337 | 0.0411 | 2600101040 lake: 194.04045 → 194.04043681080043 |
| estimate | `/ok/water/returned/peak_day/p10` | 328 | 337 | 0.0291 | 2600101040 lake: 112.5096 → 112.50960552875644 |
| estimate | `/ok/water/returned/peak_day/p50` | 328 | 337 | 0.0406 | 2600101040 lake: 147.30561 → 147.30559883989235 |
| estimate | `/ok/water/returned/peak_day/p90` | 328 | 337 | 0.045 | 2600101040 lake: 194.04045 → 194.04043681080043 |
| estimate | `/ok/water/withdrawn/avg/p10` | 328 | 337 | 0.102 | 2600101040 lake: 112.5096 → 112.50960552875644 |
| estimate | `/ok/water/withdrawn/avg/p50` | 328 | 337 | 0.0757 | 2600101040 lake: 147.30561 → 147.30559883989235 |
| estimate | `/ok/water/withdrawn/avg/p90` | 328 | 337 | 0.0653 | 2600101040 lake: 194.04045 → 194.04043681080043 |
| estimate | `/ok/water/withdrawn/peak_day/p10` | 328 | 337 | 0.0679 | 2600101040 lake: 112.5096 → 112.50960552875644 |
| estimate | `/ok/water/withdrawn/peak_day/p50` | 328 | 337 | 0.0584 | 2600101040 lake: 147.30561 → 147.30559883989235 |
| estimate | `/ok/water/withdrawn/peak_day/p90` | 328 | 337 | 0.0622 | 2600101040 lake: 194.04045 → 194.04043681080043 |
| estimate | `/ok/water/withdrawn_annual_mg/p10` | 328 | 337 | 0.102 | 2600101040 lake: 41094.131400000006 → 41094.13341937829 |
| estimate | `/ok/water/withdrawn_annual_mg/p50` | 328 | 337 | 0.0757 | 2600101040 lake: 53803.3740525 → 53803.36997627068 |
| estimate | `/ok/water/withdrawn_annual_mg/p90` | 328 | 337 | 0.0653 | 2600101040 lake: 70873.2743625 → 70873.26954514485 |
| estimate | `/ok/water/withdrawn_max_month/p10` | 328 | 337 | 0.124 | 2600101040 lake: 112.5096 → 112.50960552875644 |
| estimate | `/ok/water/withdrawn_max_month/p50` | 328 | 337 | 0.081 | 2600101040 lake: 147.30561 → 147.30559883989235 |
| estimate | `/ok/water/withdrawn_max_month/p90` | 328 | 337 | 0.0611 | 2600101040 lake: 194.04045 → 194.04043681080043 |
| estimate | `/ok/comparisons[]/percent/peak_day/p10` | 310 | 444 | 77.9 | 2600101040 lake: 4.008651402692162 → 4.008651372654401 |
| estimate | `/ok/comparisons[]/percent/peak_day/p50` | 310 | 444 | 77.9 | 2600101040 lake: 4.1892914832054355 → 4.189291362101837 |
| estimate | `/ok/comparisons[]/percent/peak_day/p90` | 310 | 444 | 77.9 | 2600101040 lake: 4.37030142156246 → 4.3703014658144435 |
| context | `/ok/energy/utilities[]/share_of_place` | 190 | 233 | 0.286 | 2600101040 context: 0.94 → 0.95 |
| context | `/ok/supply/county_use_mgd/Bottled water` | 148 | 148 | | 2605307960 context: 0.005 → "<absent>" |
| context | `/ok/wastewater/plants[]/name` | 72 | 140 | | 2600501280 context: "GRANDVILLE WWTP" → "SOUTH HAVEN STP" |
| context | `/ok/wastewater/plants[]/npdes` | 72 | 140 | | 2600501280 context: "MI0023027" → "MI0020320" |
| context | `/ok/wastewater/plants[]/flow_mgd` | 71 | 138 | 49 | 2600501280 context: null → 1.25 |
| context | `/ok/wastewater/plants[]/design_mgd` | 70 | 137 | 73.1 | 2600501280 context: 4.4 → 2.19 |
| context | `/ok/climate/region` | 68 | 68 | | 2600304460 context: "up" → "eup" |
| context | `/ok/climate/region_name` | 68 | 68 | | 2600304460 context: "Central and Western Upper Peninsula" → "Eastern Upper Peninsula" |
| context | `/ok/climate/station` | 68 | 68 | | 2600304460 context: "Marquette area" → "Pellston area" |
| reference | `/ok/salt_events[]` | 68 | 204 | 0.218 | 2600304460 reference: 35.699999999999996 → 27.9 |
| context | `/ok/wastewater/plants[]/receiving_water` | 64 | 121 | | 2600501280 context: "Grand River" → "Black River" |
| context | `/ok/receiving/basin/huc12` | 60 | 60 | 0.0418 | 2600311960 context: "04030113" → "04020201" |
| context | `/ok/receiving/basin/name` | 60 | 60 | | 2600311960 context: "Manistique River" → "Betsy-Chocolay" |
| estimate | `/ok/before_after[]/today` | 31 | 127 | 20.8 | 2601541120 assist: 0.65 → null |
| estimate | `/ok/comparisons` | 30 | 111 | | 2600528120 assist: [{"against": "county_water", "basis": "Campus water on an av → [{"against": "county_water", "name": "County", "measure": "p |
| context | `/ok/supply/nearest_system_km` | 29 | 29 | 0.0625 | 2601942000 context: 32.3 → 32.4 |
| context | `/ok/receiving/watersheds[]/huc12` | 28 | 57 | 0.0418 | 2602312560 context: "041000030203" → "040500010801" |
| context | `/ok/receiving/watersheds[]/name` | 28 | 57 | | 2602312560 context: "West Fork West Branch Saint Joseph River" → "Snow Lake" |
| context | `/ok/receiving/downstream` | 24 | 24 | | 2600347540 context: [{"assessed": true, "coldwater_streams": ["Deer Creek", "McA → [{"huc12": "040301110103", "name": "West Branch Whitefish Ri |
| context | `/ok/wastewater/plants[]/combined_sewer` | 20 | 38 | 1 | 2601730400 context: false → true |
| estimate | `/ok/comparisons[]/second_system_share` | 20 | 80 | 0.122 | 2602170960 assist: 0.32 → 0.326 |
| estimate | `/ok/site_loads[]/after` | 20 | 444 | 0.109 | 2606521420 hybrid: 45.052175260042056 → 48.81955944232305 |
| estimate | `/ok/site_loads[]/after_high` | 20 | 444 | 0.109 | 2606521420 hybrid: 97.6130463967578 → 105.77571212503327 |
| context | `/ok/supply/systems` | 19 | 19 | | 2601754980 context: [{"connections": 1388, "name": "Bangor-Monitor Metro Distric → [{"pwsid": "MI0000400", "name": "Bangor-Monitor Metro Distri |
| context | `/ok/climate/rain_in` | 17 | 17 | 0.000279 | 2612707300 context: 35.85 → 35.84 |
| estimate | `/ok/site_loads[]/after_low` | 17 | 438 | 0.000279 | 2612707300 assist: 9.660295871999999 → 9.6576012288 |
| estimate | `/ok/site_loads[]/today` | 17 | 308 | 0.000279 | 2612707300 assist: 106.41644173800002 → 106.41598571520001 |
| estimate | `/ok/site_loads[]/today_high` | 17 | 162 | 0.000279 | 2612707300 assist: 186.345897832 → 186.3453104128 |
| estimate | `/ok/site_loads[]/today_low` | 17 | 162 | 0.000279 | 2612707300 assist: 24.066040735999998 → 24.065669734399997 |
| estimate | `/ok/before_after[]/percent` | 16 | 68 | 0.954 | 2601541120 assist: 1.7299768512928189 → null |
| context | `/ok/wastewater/plants` | 14 | 14 | | 2601176120 context: [{"combined_sewer": false, "design_mgd": 0.3, "flow_mgd": 0. → [{"npdes": "MI0024139", "name": "STANDISH WWSL", "design_mgd |
| estimate | `/ok/water/to_sewer/p10` | 12 | 31 | 0.123 | 2601541120 assist: 0.00585676858841674 → 0.005435964707892472 |
| estimate | `/ok/water/to_sewer/p50` | 12 | 30 | 0.253 | 2601541120 assist: 0.011244849533403323 → 0.009853169881100108 |
| estimate | `/ok/water/to_sewer/p90` | 12 | 30 | 0.313 | 2601541120 assist: 0.02230725171712026 → 0.01994701432052491 |
| estimate | `/ok/levels/sewer` | 11 | 36 | | 2601541120 assist: "large" → "<absent>" |
| estimate | `/ok/before_after[]/key` | 9 | 32 | | 2601541120 assist: "sewer" → "wastewater" |
| estimate | `/ok/site/wastewater` | 9 | 32 | | 2601541120 assist: "sewer" → "septic" |
| estimate | `/ok/comparisons[]/name` | 7 | 40 | | 2604933300 assist: "Grand Blanc, City Of" → "Charter Township Of Grand Blanc" |
| estimate | `/ok/levels/withdrawal_mgd` | 7 | 20 | 0.0757 | 2603150300 assist: "<absent>" → 0.015329681939649774 |
| estimate | `/ok/levels/withdrawal_peak_day_mgd` | 7 | 20 | 0.0584 | 2603150300 assist: "<absent>" → 0.7193326599910423 |
| estimate | `/ok/levels/withdrawal_people` | 7 | 20 | 0.0757 | 2603150300 assist: "<absent>" → 111.23846125438169 |
| estimate | `/ok/levels/withdrawal_people_peak_day` | 7 | 20 | 0.0584 | 2603150300 assist: "<absent>" → 5219.772891729871 |
| estimate | `/ok/levels/water_system` | 6 | 18 | | 2601754980 dry: "mid" → "small" |
| context | `/ok/supply/nearest_system` | 5 | 5 | | 2603150300 context: null → {"pwsid": "MI0001360", "name": "Cheboygan, City Of", "popula |
| context | `/ok/wastewater/plants[]/lagoon` | 5 | 9 | 1 | 2605135340 context: true → false |
| estimate | `/ok/levels/withdrawal` | 5 | 14 | | 2603150300 assist: "<absent>" → "mid" |
| estimate | `/ok/levels/withdrawal_flag` | 5 | 14 | | 2603150300 assist: "<absent>" → null |
| estimate | `/ok/levels/withdrawal_flag_note` | 5 | 10 | | 2603150300 hybrid: "<absent>" → "The estimated need exceeds 1 million gallons a day. Where a |
| estimate | `/ok/levels/withdrawal_flag_peak_day` | 5 | 14 | | 2603150300 assist: "<absent>" → null |
| estimate | `/ok/levels/withdrawal_line` | 5 | 14 | | 2603150300 assist: "<absent>" → "register" |
| estimate | `/ok/levels/withdrawal_line_peak_day` | 5 | 14 | | 2603150300 assist: "<absent>" → "register" |
| estimate | `/ok/levels/withdrawal_period` | 5 | 14 | | 2603150300 assist: "<absent>" → "highest_month" |
| estimate | `/ok/site/source` | 5 | 14 | | 2603150300 assist: "muni" → "wells" |
| context | `/ok/receiving/downstream[]/huc12` | 4 | 10 | 2.49e-09 | 2602343260 context: "040500010701" → "040500010801" |
| context | `/ok/receiving/downstream[]/impairments` | 4 | 7 | | 2602343260 context: ["Water too warm", "Low oxygen", "Bacteria (E. coli)", "Chem → ["Fish and stream insects in poor shape", "Chemicals in fish |
| context | `/ok/receiving/downstream[]/name` | 4 | 10 | | 2602343260 context: "Headwaters Prairie River" → "Snow Lake" |
| estimate | `/ok/comparisons[]/second_system` | 4 | 16 | | 2604933300 assist: "Charter Township Of Grand Blanc" → "Grand Blanc, City Of" |
| context | `/ok/climate/cell` | 3 | 3 | | 2606521420 context: "42.50_-84.50" → "42.75_-84.50" |
| context | `/ok/climate/cell_land` | 3 | 3 | 0.0123 | 2606521420 context: 0.9956 → 0.9949 |
| context | `/ok/energy/utilities` | 3 | 3 | | 2600528120 context: [{"avg_mw": 4271.9, "balancing_authority": "MISO", "customer → [{"name": "Consumers Energy Company", "type": "Investor Owne |
| estimate | `/ok/electricity/peak_day_mw/p10` | 3 | 12 | 0.000811 | 2606521420 assist: 227.09406850799888 → 227.19734770770356 |
| estimate | `/ok/electricity/peak_day_mw/p50` | 3 | 12 | 0.000719 | 2606521420 assist: 277.4570978042151 → 277.5884138354472 |
| estimate | `/ok/electricity/peak_day_mw/p90` | 3 | 12 | 0.000404 | 2606521420 assist: 323.1114697810879 → 323.2420183720895 |
| estimate | `/ok/grid_water/consumed/p10` | 3 | 12 | 0.000921 | 2606521420 assist: 1.3955957208556669 → 1.3957327526750345 |
| estimate | `/ok/grid_water/consumed/p50` | 3 | 12 | 0.000996 | 2606521420 assist: 1.7193220523568384 → 1.719183906178232 |
| estimate | `/ok/grid_water/consumed/p90` | 3 | 12 | 0.00108 | 2606521420 assist: 2.0392799994374498 → 2.038491830139702 |
| estimate | `/ok/grid_water/consumed_peak_day/p10` | 3 | 12 | 0.00487 | 2606521420 assist: 1.8971477342065577 → 1.8993650316836153 |
| estimate | `/ok/grid_water/consumed_peak_day/p50` | 3 | 12 | 0.00202 | 2606521420 assist: 2.291867433035309 → 2.29391976719534 |
| estimate | `/ok/grid_water/consumed_peak_day/p90` | 3 | 12 | 0.00183 | 2606521420 assist: 2.6786609276271225 → 2.68180632700316 |
| estimate | `/ok/grid_water/marginal_consumed/p10` | 3 | 12 | 0.00059 | 2606521420 assist: 1.242639667785944 → 1.242490042073722 |
| estimate | `/ok/grid_water/marginal_consumed/p50` | 3 | 12 | 0.000668 | 2606521420 assist: 1.5305118445082941 → 1.5300641838475482 |
| estimate | `/ok/grid_water/marginal_consumed/p90` | 3 | 12 | 0.000811 | 2606521420 assist: 1.8153270579750431 → 1.814208168643991 |
| estimate | `/ok/grid_water/marginal_consumed_peak_day/p10` | 3 | 12 | 0.00482 | 2606521420 assist: 1.6254289072311079 → 1.6273954150993797 |
| estimate | `/ok/grid_water/marginal_consumed_peak_day/p50` | 3 | 12 | 0.00482 | 2606521420 assist: 1.9951185571017942 → 1.999320396715034 |
| estimate | `/ok/grid_water/marginal_consumed_peak_day/p90` | 3 | 12 | 0.00481 | 2606521420 assist: 2.3257981834703276 → 2.328496997895317 |
| estimate | `/ok/grid_water/marginal_withdrawn/p10` | 3 | 12 | 0.000668 | 2606521420 assist: 56.28833486993471 → 56.27646526426798 |
| estimate | `/ok/grid_water/marginal_withdrawn/p50` | 3 | 12 | 0.000685 | 2606521420 assist: 69.32076996904469 → 69.29437614424026 |
| estimate | `/ok/grid_water/marginal_withdrawn/p90` | 3 | 12 | 0.00084 | 2606521420 assist: 82.21109646147758 → 82.15231772601744 |
| estimate | `/ok/grid_water/marginal_withdrawn_peak_day/p10` | 3 | 12 | 0.0246 | 2606521420 assist: 81.38720737318081 → 79.38677542278721 |
| estimate | `/ok/grid_water/marginal_withdrawn_peak_day/p50` | 3 | 12 | 0.0254 | 2606521420 assist: 99.83633607470216 → 97.2995344780789 |
| estimate | `/ok/grid_water/marginal_withdrawn_peak_day/p90` | 3 | 12 | 0.0267 | 2606521420 assist: 116.94671694104161 → 113.82047648601932 |
| estimate | `/ok/grid_water/withdrawn/p10` | 3 | 12 | 0.000872 | 2606521420 assist: 55.15460312981664 → 55.15896469201557 |
| estimate | `/ok/grid_water/withdrawn/p50` | 3 | 12 | 0.000981 | 2606521420 assist: 67.94790127600166 → 67.94089534101084 |
| estimate | `/ok/grid_water/withdrawn/p90` | 3 | 12 | 0.00106 | 2606521420 assist: 80.58254621701647 → 80.54894676515748 |
| estimate | `/ok/grid_water/withdrawn_peak_day/p10` | 3 | 12 | 0.00477 | 2606521420 assist: 75.22751472961563 → 75.35482817429506 |
| estimate | `/ok/grid_water/withdrawn_peak_day/p50` | 3 | 12 | 0.00317 | 2606521420 assist: 91.15852568914926 → 91.34123682274375 |
| estimate | `/ok/grid_water/withdrawn_peak_day/p90` | 3 | 12 | 0.00387 | 2606521420 assist: 106.43072125514695 → 106.70454247421011 |
| estimate | `/ok/water/blowdown/p10` | 3 | 9 | 0.138 | 2606521420 assist: 0.0013724473083280573 → 0.0014259197345304012 |
| estimate | `/ok/water/blowdown/p50` | 3 | 9 | 0.136 | 2606521420 assist: 0.0031592626614559225 → 0.0034587603924365017 |
| estimate | `/ok/water/blowdown/p90` | 3 | 9 | 0.1 | 2606521420 assist: 0.01032516410660686 → 0.011238127444499858 |
| estimate | `/ok/water/condensate/avg/p10` | 3 | 12 | 0.0673 | 2606521420 assist: 0.0004143306324703955 → 0.0003864380195595317 |
| estimate | `/ok/water/condensate/avg/p50` | 3 | 12 | 0.0673 | 2606521420 assist: 0.0013702713715866427 → 0.0012780251171337197 |
| estimate | `/ok/water/condensate/avg/p90` | 3 | 12 | 0.0673 | 2606521420 assist: 0.002323929741553875 → 0.002167483493959962 |
| estimate | `/ok/water/condensate/peak_day/p10` | 3 | 12 | 0.0268 | 2606521420 assist: 0.006748922878968521 → 0.006691967345077975 |
| estimate | `/ok/water/condensate/peak_day/p50` | 3 | 12 | 0.0268 | 2606521420 assist: 0.022319990571195446 → 0.0221316276276247 |
| estimate | `/ok/water/condensate/peak_day/p90` | 3 | 12 | 0.0268 | 2606521420 assist: 0.03785388135164976 → 0.03753442474192446 |
| estimate | `/ok/water/withdrawn_peak_full_capacity/p10` | 3 | 12 | 0.0819 | 2606521420 assist: 0.8298544082699875 → 0.8285834478175558 |
| estimate | `/ok/water/withdrawn_peak_full_capacity/p50` | 3 | 12 | 0.0569 | 2606521420 assist: 1.1610701350718262 → 1.1687552366065619 |
| estimate | `/ok/water/withdrawn_peak_full_capacity/p90` | 3 | 12 | 0.0662 | 2606521420 assist: 1.713950729591407 → 1.8017595767011299 |
| context | `/ok/climate/cell_moved` | 2 | 2 | 1 | 2601180840 context: true → false |
| context | `/ok/receiving/downstream[]/coldwater_streams` | 2 | 2 | | 2602343260 context: ["Prairie River"] → [] |
| context | `/ok/receiving/downstream[]/tmdl` | 2 | 4 | | 2602343260 context: ["Bacteria (E. coli)", "Chemicals in fish (mercury, PCBs, PF → [] |
| context | `/ok/supply/systems[]/connections` | 2 | 4 | 9.57 | 2601705120 context: 5138 → 486 |
| context | `/ok/supply/systems[]/name` | 2 | 4 | | 2601705120 context: "Bangor Township" → "Pinconning Township" |
| context | `/ok/supply/systems[]/population` | 2 | 4 | 7.11 | 2601705120 context: 11999 → 1479 |
| context | `/ok/supply/systems[]/pwsid` | 2 | 4 | | 2601705120 context: "MI0000390" → "MI0005335" |
| context | `/ok/energy/nearest_place_km` | 1 | 1 | 1 | 2602970920 context: 22.1 → 0.0 |
| context | `/ok/energy/nearest_utilities[]/avg_mw` | 1 | 1 | 0.000199 | 2602970920 context: 189.2 → 189.16244292237442 |
| context | `/ok/energy/utilities[]/customers` | 1 | 2 | 68.7 | 2606765860 context: 27298 → 1901950 |
| context | `/ok/energy/utilities[]/name` | 1 | 2 | | 2606765860 context: "Homeworks Tri-County Electric Cooperative" → "Consumers Energy Company" |
| context | `/ok/energy/utilities[]/summer_peak_mw` | 1 | 2 | 77.9 | 2606765860 context: 100.7 → 7949.0 |
| context | `/ok/energy/utilities[]/type` | 1 | 2 | | 2606765860 context: "Cooperative" → "Investor Owned" |
| context | `/ok/wastewater/plants[]/own` | 1 | 1 | | 2606546000 context: false → true |
| context | `/ok/wastewater/plants[]/system` | 1 | 1 | | 2612517640 context: false → true |
