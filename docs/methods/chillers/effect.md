# Design 0021: model 1.16 against the chiller change alone

In memory, the same draws, seed and station correction; 100 MW of IT; p50. Made with `effect.py` from the cell runs `docs/research/cooling-power-evidence/phoenix_run.py` writes, on commit f8a218f.

| Place | Plant | Design | PUE a year, 1.16 → 1.17 | hottest-hour PUE, 1.16 → 1.17 | hottest hour, MW, 1.16 → 1.17 | evaporated, MGD, 1.16 → 1.17 |
|---|---|---|---|---|---|---|
| Grand Rapids | shared | dry | 1.175 → 1.175 | 1.343 → 1.340 | 134.3 → 134.0 | 0.000 → 0.000 |
| Grand Rapids | shared | hybrid | 1.175 → 1.174 | 1.306 → 1.304 | 130.6 → 130.4 | 0.007 → 0.007 |
| Grand Rapids | shared | towers | 1.137 → 1.134 | 1.269 → 1.257 | 126.9 → 125.7 | 0.524 → 0.522 |
| Grand Rapids | chilled | dry | 1.277 → 1.276 | 1.458 → 1.455 | 145.8 → 145.5 | 0.000 → 0.000 |
| Grand Rapids | chilled | hybrid | 1.275 → 1.275 | 1.415 → 1.413 | 141.5 → 141.3 | 0.008 → 0.008 |
| Grand Rapids | chilled | towers | 1.221 → 1.217 | 1.342 → 1.342 | 134.2 → 134.2 | 0.563 → 0.561 |
| Grand Rapids | warm | dry | 1.134 → 1.134 | 1.291 → 1.290 | 129.1 → 129.0 | 0.000 → 0.000 |
| Grand Rapids | warm | hybrid | 1.132 → 1.132 | 1.226 → 1.225 | 122.6 → 122.5 | 0.007 → 0.007 |
| Grand Rapids | warm | towers | 1.114 → 1.113 | 1.179 → 1.173 | 117.9 → 117.3 | 0.514 → 0.514 |
| Loudoun County | shared | dry | 1.192 → 1.192 | 1.356 → 1.352 | 135.6 → 135.2 | 0.000 → 0.000 |
| Loudoun County | shared | hybrid | 1.191 → 1.190 | 1.306 → 1.304 | 130.6 → 130.4 | 0.013 → 0.013 |
| Loudoun County | shared | towers | 1.150 → 1.142 | 1.268 → 1.255 | 126.8 → 125.5 | 0.541 → 0.539 |
| Loudoun County | chilled | dry | 1.304 → 1.303 | 1.470 → 1.467 | 147.0 → 146.7 | 0.000 → 0.000 |
| Loudoun County | chilled | hybrid | 1.301 → 1.300 | 1.415 → 1.414 | 141.5 → 141.4 | 0.014 → 0.014 |
| Loudoun County | chilled | towers | 1.237 → 1.233 | 1.338 → 1.339 | 133.8 → 133.9 | 0.584 → 0.584 |
| Loudoun County | warm | dry | 1.143 → 1.143 | 1.301 → 1.300 | 130.1 → 130.0 | 0.000 → 0.000 |
| Loudoun County | warm | hybrid | 1.141 → 1.141 | 1.226 → 1.225 | 122.6 → 122.5 | 0.012 → 0.012 |
| Loudoun County | warm | towers | 1.120 → 1.117 | 1.177 → 1.169 | 117.7 → 116.9 | 0.527 → 0.526 |
| Dallas | shared | dry | 1.233 → 1.233 | 1.378 → 1.377 | 137.8 → 137.7 | 0.000 → 0.000 |
| Dallas | shared | hybrid | 1.228 → 1.226 | 1.309 → 1.306 | 130.9 → 130.6 | 0.044 → 0.044 |
| Dallas | shared | towers | 1.176 → 1.163 | 1.269 → 1.258 | 126.9 → 125.8 | 0.583 → 0.577 |
| Dallas | chilled | dry | 1.351 → 1.349 | 1.494 → 1.492 | 149.4 → 149.2 | 0.000 → 0.000 |
| Dallas | chilled | hybrid | 1.342 → 1.341 | 1.415 → 1.414 | 141.5 → 141.4 | 0.047 → 0.047 |
| Dallas | chilled | towers | 1.268 → 1.265 | 1.343 → 1.343 | 134.3 → 134.3 | 0.631 → 0.630 |
| Dallas | warm | dry | 1.170 → 1.170 | 1.317 → 1.316 | 131.7 → 131.6 | 0.000 → 0.000 |
| Dallas | warm | hybrid | 1.163 → 1.162 | 1.232 → 1.229 | 123.2 → 122.9 | 0.040 → 0.040 |
| Dallas | warm | towers | 1.129 → 1.125 | 1.180 → 1.173 | 118.0 → 117.3 | 0.561 → 0.559 |
| Phoenix | shared | dry | 1.258 → 1.257 | 1.404 → 1.403 | 140.4 → 140.3 | 0.000 → 0.000 |
| Phoenix | shared | hybrid | 1.246 → 1.241 | 1.314 → 1.308 | 131.4 → 130.8 | 0.099 → 0.098 |
| Phoenix | shared | towers | 1.152 → 1.144 | 1.268 → 1.255 | 126.8 → 125.5 | 0.594 → 0.592 |
| Phoenix | chilled | dry | 1.379 → 1.377 | 1.524 → 1.520 | 152.4 → 152.0 | 0.000 → 0.000 |
| Phoenix | chilled | hybrid | 1.358 → 1.357 | 1.416 → 1.414 | 141.6 → 141.4 | 0.105 → 0.105 |
| Phoenix | chilled | towers | 1.269 → 1.260 | 1.339 → 1.340 | 133.9 → 134.0 | 0.655 → 0.651 |
| Phoenix | warm | dry | 1.193 → 1.193 | 1.339 → 1.338 | 133.9 → 133.8 | 0.000 → 0.000 |
| Phoenix | warm | hybrid | 1.171 → 1.168 | 1.239 → 1.233 | 123.9 → 123.3 | 0.091 → 0.090 |
| Phoenix | warm | towers | 1.120 → 1.118 | 1.177 → 1.170 | 117.7 → 117.0 | 0.580 → 0.579 |
