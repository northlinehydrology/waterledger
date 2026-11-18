# Design 0022's check: the outside air design at four places (model 1.17 code, in memory)

Made by `check_outside_air.py` on commit ebbf55a: 30 years of each cell's station-corrected ERA5 weather, 400 draws (seed 7), shared plant; median (10th-90th percentile) over the draws. WUE is per IT kWh. The hottest hour is the 90th percentile of the years' highest hourly PUE at the peak-day load.

| Place | Halls | PUE a year | Hottest-hour PUE | WUE consumed, L/kWh | WUE withdrawn, L/kWh | Hours on pads | Hours with trim chillers |
|---|---|---|---|---|---|---|---|
| Grand Rapids, MI | all air-cooled | 1.107 (1.052-1.163) | 1.115 (1.061-1.172) | 0.01 (0.00-0.01) | 0.01 (0.00-0.02) | 1% (1-4) | 0% (0-0) |
| Grand Rapids, MI | plant's liquid share | 1.122 (1.064-1.185) | 1.191 (1.106-1.274) | 0.00 (0.00-0.01) | 0.00 (0.00-0.01) | 1% (1-4) | 0% (0-0) |
| Loudoun County, VA | all air-cooled | 1.107 (1.052-1.163) | 1.112 (1.057-1.170) | 0.01 (0.01-0.03) | 0.01 (0.01-0.03) | 4% (2-8) | 0% (0-0) |
| Loudoun County, VA | plant's liquid share | 1.127 (1.066-1.194) | 1.191 (1.106-1.280) | 0.01 (0.00-0.02) | 0.01 (0.00-0.02) | 4% (2-8) | 0% (0-0) |
| Dallas, TX | all air-cooled | 1.107 (1.052-1.163) | 1.124 (1.066-1.187) | 0.06 (0.04-0.11) | 0.08 (0.05-0.13) | 15% (10-23) | 0% (0-3) |
| Dallas, TX | plant's liquid share | 1.142 (1.076-1.215) | 1.208 (1.117-1.296) | 0.04 (0.02-0.07) | 0.05 (0.02-0.09) | 15% (10-23) | 0% (0-3) |
| Phoenix, AZ | all air-cooled | 1.107 (1.052-1.163) | 1.119 (1.063-1.175) | 0.20 (0.14-0.30) | 0.25 (0.17-0.38) | 32% (26-39) | 0% (0-1) |
| Phoenix, AZ | plant's liquid share | 1.150 (1.082-1.228) | 1.212 (1.118-1.309) | 0.12 (0.06-0.21) | 0.15 (0.07-0.27) | 32% (26-39) | 0% (0-1) |

The same draws, the plant's liquid share:

| Place | Design | PUE a year | Hottest-hour PUE | WUE consumed, L/kWh | WUE withdrawn, L/kWh |
|---|---|---|---|---|---|
| Grand Rapids, MI | dry | 1.175 (1.099-1.259) | 1.340 (1.261-1.428) | 0.00 (0.00-0.00) | 0.00 (0.00-0.00) |
| Grand Rapids, MI | towers | 1.134 (1.072-1.210) | 1.256 (1.174-1.343) | 1.26 (1.14-1.40) | 1.61 (1.43-1.84) |
| Loudoun County, VA | dry | 1.192 (1.111-1.278) | 1.352 (1.271-1.441) | 0.00 (0.00-0.00) | 0.00 (0.00-0.00) |
| Loudoun County, VA | towers | 1.142 (1.076-1.222) | 1.254 (1.170-1.341) | 1.30 (1.18-1.44) | 1.66 (1.48-1.91) |
| Dallas, TX | dry | 1.233 (1.146-1.323) | 1.377 (1.291-1.466) | 0.00 (0.00-0.00) | 0.00 (0.00-0.00) |
| Dallas, TX | towers | 1.163 (1.088-1.248) | 1.257 (1.176-1.344) | 1.39 (1.26-1.54) | 1.78 (1.58-2.04) |
| Phoenix, AZ | dry | 1.257 (1.169-1.349) | 1.403 (1.314-1.495) | 0.00 (0.00-0.00) | 0.00 (0.00-0.00) |
| Phoenix, AZ | towers | 1.144 (1.077-1.226) | 1.255 (1.172-1.341) | 1.43 (1.30-1.57) | 1.82 (1.63-2.08) |
