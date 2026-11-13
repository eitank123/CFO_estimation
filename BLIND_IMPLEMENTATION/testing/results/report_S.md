# S experiments: fast path off, per-hypothesis cores, speculative decode, nph15 (analysis 2026-11-12)

Analysis only (no simulation). Tables: `py BLIND_IMPLEMENTATION/testing/agg_S.py`; plots: `py BLIND_IMPLEMENTATION/testing/plot_S.py`.
Predictions: `BLIND_IMPLEMENTATION/testing/README.md`, "S experiments". MACs per core = crit_par (the standard 32-core model).

## Validation

| job | log | parts | packets per (point, receiver) | status |
|---|---|---|---|---|
| nf10a | EVAL DONE, ALL DONE, 0 Traceback | nf10a | 16 x 4000 = 64000 (requested 64000) | ok |
| nf10b | EVAL DONE, ALL DONE, 0 Traceback | nf10b | 64000 | ok |
| nf15a | EVAL DONE, ALL DONE, 0 Traceback | nf15a | 64000 | ok |
| nf15b | 2 x EVAL DONE, ALL DONE, 0 Traceback | nf15b, nf15c | 64000 | ok |
| nn15a | EVAL DONE, ALL DONE, 0 Traceback | nn15a (noise only, -1 dB) | 16 x 700 = 11200 (requested 16 x 625 = 10000) | ok, see note 1 |
| nn15b | 2 x EVAL DONE, ALL DONE, 0 Traceback | nn15b (noise only, 0 dB), nn15c (signal, +1 dB) | 11200 / 64000 | ok, see notes 1, 2 |

Notes on the data:
1. Noise-only chunks hold 700 packets, not 625: blind_ber simulates in batches of 100, so `--max-frames 625` stops at 700.
   Each noise-only arm has 11 200 packets per SNR (22 400 over the two SNRs).
2. `nn15c` is NOT noise-only: it is the signal-present +1 dB cost run (64 000 paired packets, base10 vs nph15). The
   noise-only data are -1 dB (nn15a) and 0 dB (nn15b) only, 11 200 packets each; there is no noise-only run at +1 dB
   and no 64k noise-only run.
3. Smoke parts (`nf-smoke-a/b/c`, seed 7899) are excluded everywhere.
4. The baseline arms of nf10a (1/10 -5, -4 dB) and nf15a / nf15b (0.15 -4, -3 dB) are the SAME packets as srch10 /
   srch15 (seed 7701 / 7702, same chunking): never merge these parts with srch10 / srch15 (duplicated packets).
5. The parts store one row per (chunk, receiver), no per-packet outcomes: paired BLER is per chunk of 4000 packets
   ("fixed / broken" are lower bounds from chunks where the variant has fewer / more errors), not per packet.
   Pairing inside each part was checked (out_coarse_1e3, a function of the packets only, is equal chunk by chunk).
6. No nofast run against the baseline receiver at R = 0.15 above -3 dB: -1 and 0 dB compare nofast_nph4 with nph4.
   nofast_spec exists only at 1/10 -5, -4 dB and 0.15 -4, -3 dB. nofast was not run above 0 dB.
7. The rows of a part are in completion order, not chunk order (the errors per chunk rise along the file; a likely
   reason is that chunks with failed packets cost more and finish later). Not verified: the rows carry no chunk seed.

**The "out" rule under nofast.** `frame_err` compares the delivered data with the truth, and a packet without an
accepted decode delivers its first decode (`out` in `small_rx.decode`): the fast-path decode in the baseline, the
first search decode under nofast. An unaccepted but right first decode (a `check_lost` case that is never accepted
later) would be no frame error, under a rule that differs between the arms. So every table also has `miss` = packets
without an accepted and right decode (frames - n_dd), the same rule in every arm. Result: `miss` = `frame_err` at
every point and receiver, so the rule made no difference in these runs; the BLER columns can be compared directly.

**Baseline sanity check.** The baseline arm reproduces the R runs exactly, not only roughly: 8 / 64000 at 1/10 -5 dB,
0 at -4 dB, 273 / 64000 and 7 / 64000 at 0.15 -4 / -3 dB, and the 16 chunks agree one by one in errors, total MACs and
crit_par MACs (table "Baseline arm vs the R runs").

## Tables

Per core 99 % / 99.9 % / max: upper edge of the 0.05-decade histogram bin (all packets). +- = 95 % from the 16 paired chunks.

### Results (signal present)

| R | SNR | receiver | errors / packets | BLER (95 % CI) | miss | undetected | total [M] | per core [M] | crit_par_h [M] | per core 99 % / 99.9 % / max [M] | dec/pk | spec dec / pass | check_lost | part |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1/10 | -5 | S blind final v2 | 8 / 64000 | 1.25e-04 [5.4e-05, 2.5e-04] | 8 | 0 | 4.131 | 0.310 | 0.275 | 0.56 / 0.89 / 35.48 | 3.27 | - | 0 | nf10a |
| 1/10 | -5 | T nofast | 8 / 64000 | 1.25e-04 [5.4e-05, 2.5e-04] | 8 | 0 | 3.631 | 0.216 | 0.180 | 0.45 / 0.79 / 35.48 | 1.29 | - | 0 | nf10a |
| 1/10 | -5 | T nofast_spec | 9 / 64000 | 1.41e-04 [6.4e-05, 2.7e-04] | 9 | 1 | 2.978 | 0.194 | 0.160 | 0.50 / 0.79 / 35.48 | 1.45 | 27460 / 17101 | 0 | nf10a |
| 1/10 | -4 | S blind final v2 | 0 / 64000 | < 4.7e-05 | 0 | 0 | 2.987 | 0.258 | 0.226 | 0.50 / 0.63 / 1.12 | 3.04 | - | 1 | nf10a |
| 1/10 | -4 | T nofast | 0 / 64000 | < 4.7e-05 | 0 | 0 | 2.485 | 0.163 | 0.131 | 0.40 / 0.56 / 1.00 | 1.08 | - | 0 | nf10a |
| 1/10 | -4 | T nofast_spec | 0 / 64000 | < 4.7e-05 | 0 | 0 | 2.342 | 0.162 | 0.129 | 0.45 / 0.63 / 1.00 | 1.22 | 15421 / 6274 | 0 | nf10a |
| 1/10 | -3 | S blind final v2 | 0 / 64000 | < 4.7e-05 | 0 | 0 | 2.669 | 0.243 | 0.212 | 0.50 / 0.71 / 1.00 | 3.01 | - | 0 | nf10b |
| 1/10 | -3 | T nofast | 0 / 64000 | < 4.7e-05 | 0 | 0 | 2.187 | 0.150 | 0.119 | 0.40 / 0.56 / 0.89 | 1.08 | - | 0 | nf10b |
| 1/10 | -1 | S blind final v2 | 0 / 64000 | < 4.7e-05 | 0 | 0 | 1.946 | 0.202 | 0.180 | 0.50 / 0.63 / 1.26 | 2.76 | - | 3 | nf10b |
| 1/10 | -1 | T nofast | 0 / 64000 | < 4.7e-05 | 0 | 0 | 1.592 | 0.127 | 0.104 | 0.40 / 0.56 / 1.26 | 1.13 | - | 0 | nf10b |
| 1/10 | 0 | S blind final v2 | 0 / 64000 | < 4.7e-05 | 0 | 0 | 1.437 | 0.153 | 0.140 | 0.45 / 0.63 / 0.89 | 2.22 | - | 2 | nf10b |
| 1/10 | 0 | T nofast | 0 / 64000 | < 4.7e-05 | 0 | 0 | 1.302 | 0.108 | 0.091 | 0.32 / 0.50 / 0.79 | 1.10 | - | 0 | nf10b |
| 0.15 | -4 | S blind final v2 | 273 / 64000 | 4.27e-03 [3.8e-03, 4.8e-03] | 273 | 0 | 7.368 | 0.650 | 0.608 | 8.91 / 39.81 / 39.81 | 10.14 | - | 0 | nf15a |
| 0.15 | -4 | T nofast | 275 / 64000 | 4.30e-03 [3.8e-03, 4.8e-03] | 275 | 0 | 6.888 | 0.551 | 0.509 | 8.91 / 39.81 / 39.81 | 8.20 | - | 0 | nf15a |
| 0.15 | -4 | T nofast_spec | 275 / 64000 | 4.30e-03 [3.8e-03, 4.8e-03] | 275 | 0 | 6.245 | 0.529 | 0.489 | 8.91 / 39.81 / 39.81 | 8.31 | 25665 / 14377 | 0 | nf15a |
| 0.15 | -3 | S blind final v2 | 7 / 64000 | 1.09e-04 [4.4e-05, 2.3e-04] | 7 | 0 | 3.295 | 0.282 | 0.246 | 0.56 / 0.71 / 39.81 | 3.12 | - | 0 | nf15b |
| 0.15 | -3 | T nofast | 7 / 64000 | 1.09e-04 [4.4e-05, 2.3e-04] | 7 | 0 | 2.812 | 0.183 | 0.148 | 0.45 / 0.63 / 39.81 | 1.18 | - | 0 | nf15b |
| 0.15 | -3 | T nofast_spec | 7 / 64000 | 1.09e-04 [4.4e-05, 2.3e-04] | 7 | 0 | 2.615 | 0.180 | 0.144 | 0.45 / 0.71 / 39.81 | 1.32 | 14812 / 6109 | 0 | nf15b |
| 0.15 | -1 | T nph4 | 0 / 64000 | < 4.7e-05 | 0 | 0 | 2.375 | 0.224 | 0.197 | 0.50 / 0.71 / 1.00 | 2.72 | - | 0 | nf15c |
| 0.15 | -1 | T nofast_nph4 | 0 / 64000 | < 4.7e-05 | 0 | 0 | 2.084 | 0.145 | 0.116 | 0.40 / 0.56 / 0.89 | 1.06 | - | 0 | nf15c |
| 0.15 | 0 | T nph4 | 0 / 64000 | < 4.7e-05 | 0 | 0 | 1.767 | 0.171 | 0.154 | 0.40 / 0.63 / 1.00 | 2.20 | - | 7 | nf15c |
| 0.15 | 0 | T nofast_nph4 | 0 / 64000 | < 4.7e-05 | 0 | 0 | 1.821 | 0.127 | 0.104 | 0.32 / 0.50 / 0.79 | 1.04 | - | 0 | nf15c |
| 0.15 | 1 | S blind final v2 | 0 / 64000 | < 4.7e-05 | 0 | 0 | 0.884 | 0.099 | 0.094 | 0.32 / 0.56 / 1.26 | 1.47 | - | 4 | nn15c |
| 0.15 | 1 | T nph15 | 0 / 64000 | < 4.7e-05 | 0 | 0 | 0.973 | 0.101 | 0.095 | 0.32 / 0.50 / 0.89 | 1.46 | - | 1 | nn15c |

### Paired differences vs the job's baseline arm (same packets; +- = 95 % from the 16 paired chunks)

| R | SNR | receiver vs baseline | errors (var vs base) | chunk-paired fixed / broken | miss (var vs base) | total | per core | crit_par_h vs base crit_par | grid crit | stage 1 share of base | pairing ok |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1/10 | -5 | T nofast vs S blind final v2 | 8 vs 8 | 0 / 0 | 8 vs 8 | -12.1 +- 0.1 % | -30.5 +- 0.4 % | -42.0 % | +1.0 % | 1.3 % | True |
| 1/10 | -5 | T nofast_spec vs S blind final v2 | 9 vs 8 | 0 / 1 | 9 vs 8 | -27.9 +- 0.4 % | -37.5 +- 0.5 % | -48.5 % | -19.5 % | 1.3 % | True |
| 1/10 | -4 | T nofast vs S blind final v2 | 0 vs 0 | 0 / 0 | 0 vs 0 | -16.8 +- 0.1 % | -36.6 +- 0.1 % | -49.2 % | +1.3 % | 2.0 % | True |
| 1/10 | -4 | T nofast_spec vs S blind final v2 | 0 vs 0 | 0 / 0 | 0 vs 0 | -21.6 +- 0.2 % | -37.3 +- 0.1 % | -49.8 % | -7.8 % | 2.0 % | True |
| 1/10 | -3 | T nofast vs S blind final v2 | 0 vs 0 | 0 / 0 | 0 vs 0 | -18.1 +- 0.1 % | -38.0 +- 0.1 % | -50.8 % | +2.1 % | 3.5 % | True |
| 1/10 | -1 | T nofast vs S blind final v2 | 0 vs 0 | 0 / 0 | 0 vs 0 | -18.2 +- 0.1 % | -37.1 +- 0.1 % | -48.6 % | +8.4 % | 17.7 % | True |
| 1/10 | 0 | T nofast vs S blind final v2 | 0 vs 0 | 0 / 0 | 0 vs 0 | -9.4 +- 0.2 % | -29.7 +- 0.2 % | -40.8 % | +26.2 % | 42.6 % | True |
| 0.15 | -4 | T nofast vs S blind final v2 | 275 vs 273 | 0 / 2 | 275 vs 273 | -6.5 +- 0.2 % | -15.2 +- 0.6 % | -21.6 % | +1.2 % | 1.5 % | True |
| 0.15 | -4 | T nofast_spec vs S blind final v2 | 275 vs 273 | 0 / 2 | 275 vs 273 | -15.2 +- 0.5 % | -18.6 +- 0.8 % | -24.7 % | -14.8 % | 1.5 % | True |
| 0.15 | -3 | T nofast vs S blind final v2 | 7 vs 7 | 0 / 0 | 7 vs 7 | -14.7 +- 0.2 % | -34.9 +- 0.4 % | -47.6 % | +1.9 % | 3.0 % | True |
| 0.15 | -3 | T nofast_spec vs S blind final v2 | 7 vs 7 | 0 / 0 | 7 vs 7 | -20.6 +- 0.3 % | -36.3 +- 0.4 % | -48.8 % | -8.1 % | 3.0 % | True |
| 0.15 | -1 | T nofast_nph4 vs T nph4 | 0 vs 0 | 0 / 0 | 0 vs 0 | -12.2 +- 0.2 % | -35.2 +- 0.2 % | -48.2 % | +9.8 % | 17.0 % | True |
| 0.15 | 0 | T nofast_nph4 vs T nph4 | 0 vs 0 | 0 / 0 | 0 vs 0 | +3.1 +- 0.3 % | -26.0 +- 0.2 % | -39.1 % | +33.6 % | 41.6 % | True |
| 0.15 | 1 | T nph15 vs S blind final v2 | 0 vs 0 | 0 / 0 | 0 vs 0 | +10.1 +- 0.4 % | +2.1 +- 0.2 % | -3.6 % | +21.7 % | 77.9 % | True |

### S2: nofast_spec vs nofast

| R | SNR | errors (spec vs nofast) | total | per core | dec/pk | spec decodes / pk | spec pass share |
|---|---|---|---|---|---|---|---|
| 1/10 | -5 | 9 vs 8 | -18.0 +- 0.4 % | -10.0 +- 0.3 % | 1.45 vs 1.29 (+0.16) | 0.429 | 62.3% |
| 1/10 | -4 | 0 vs 0 | -5.8 +- 0.2 % | -1.2 +- 0.2 % | 1.22 vs 1.08 (+0.14) | 0.241 | 40.7% |
| 0.15 | -4 | 275 vs 275 | -9.3 +- 0.3 % | -4.0 +- 0.3 % | 8.31 vs 8.20 (+0.11) | 0.401 | 56.0% |
| 0.15 | -3 | 7 vs 7 | -7.0 +- 0.3 % | -2.1 +- 0.2 % | 1.32 vs 1.18 (+0.14) | 0.231 | 41.2% |

### S1b: crit_par_h vs crit_par within each receiver

| R | SNR | receiver | crit_par [M] | crit_par_h [M] | change | grid part: crit_grid -> per-hypothesis |
|---|---|---|---|---|---|---|
| 1/10 | -5 | S blind final v2 | 0.310 | 0.275 | -11.4 % | 0.143 -> 0.108 (-24.6 %) |
| 1/10 | -5 | T nofast | 0.216 | 0.180 | -16.5 % | 0.145 -> 0.109 (-24.6 %) |
| 1/10 | -5 | T nofast_spec | 0.194 | 0.160 | -17.7 % | 0.115 -> 0.081 (-29.7 %) |
| 1/10 | -4 | S blind final v2 | 0.258 | 0.226 | -12.5 % | 0.100 -> 0.068 (-32.1 %) |
| 1/10 | -4 | T nofast | 0.163 | 0.131 | -19.9 % | 0.102 -> 0.069 (-32.1 %) |
| 1/10 | -4 | T nofast_spec | 0.162 | 0.129 | -19.9 % | 0.093 -> 0.060 (-34.7 %) |
| 1/10 | -3 | S blind final v2 | 0.243 | 0.212 | -12.6 % | 0.087 -> 0.056 (-35.1 %) |
| 1/10 | -3 | T nofast | 0.150 | 0.119 | -20.7 % | 0.089 -> 0.058 (-35.1 %) |
| 1/10 | -1 | S blind final v2 | 0.202 | 0.180 | -10.6 % | 0.058 -> 0.037 (-36.8 %) |
| 1/10 | -1 | T nofast | 0.127 | 0.104 | -18.2 % | 0.063 -> 0.040 (-36.7 %) |
| 1/10 | 0 | S blind final v2 | 0.153 | 0.140 | -8.7 % | 0.036 -> 0.022 (-37.5 %) |
| 1/10 | 0 | T nofast | 0.108 | 0.091 | -15.7 % | 0.045 -> 0.028 (-37.6 %) |
| 0.15 | -4 | S blind final v2 | 0.650 | 0.608 | -6.4 % | 0.179 -> 0.138 (-23.1 %) |
| 0.15 | -4 | T nofast | 0.551 | 0.509 | -7.6 % | 0.181 -> 0.139 (-23.1 %) |
| 0.15 | -4 | T nofast_spec | 0.529 | 0.489 | -7.6 % | 0.153 -> 0.113 (-26.3 %) |
| 0.15 | -3 | S blind final v2 | 0.282 | 0.246 | -12.5 % | 0.112 -> 0.077 (-31.5 %) |
| 0.15 | -3 | T nofast | 0.183 | 0.148 | -19.6 % | 0.114 -> 0.078 (-31.5 %) |
| 0.15 | -3 | T nofast_spec | 0.180 | 0.144 | -19.6 % | 0.103 -> 0.068 (-34.3 %) |
| 0.15 | -1 | T nph4 | 0.224 | 0.197 | -11.9 % | 0.074 -> 0.047 (-36.2 %) |
| 0.15 | -1 | T nofast_nph4 | 0.145 | 0.116 | -20.0 % | 0.081 -> 0.052 (-36.0 %) |
| 0.15 | 0 | T nph4 | 0.171 | 0.154 | -10.0 % | 0.048 -> 0.030 (-36.1 %) |
| 0.15 | 0 | T nofast_nph4 | 0.127 | 0.104 | -17.7 % | 0.064 -> 0.041 (-35.4 %) |
| 0.15 | 1 | S blind final v2 | 0.099 | 0.094 | -4.9 % | 0.013 -> 0.008 (-37.4 %) |
| 0.15 | 1 | T nph15 | 0.101 | 0.095 | -5.6 % | 0.016 -> 0.010 (-35.7 %) |

### Baseline arm vs the R runs (same seed and chunking)

| R | SNR | S baseline errors / packets | R run errors / packets | chunks identical (errors and MACs) | total S / R [M] | per core S / R [M] |
|---|---|---|---|---|---|---|
| 1/10 | -5 | 8 / 64000 | 8 / 64000 | True | 4.131 / 4.131 | 0.310 / 0.310 |
| 1/10 | -4 | 0 / 64000 | 0 / 64000 | True | 2.987 / 2.987 | 0.258 / 0.258 |
| 1/10 | -3 | 0 / 64000 | not in srch10 | - | - | - |
| 1/10 | -1 | 0 / 64000 | not in srch10 | - | - | - |
| 1/10 | 0 | 0 / 64000 | not in srch10 | - | - | - |
| 0.15 | -4 | 273 / 64000 | 273 / 64000 | True | 7.368 / 7.368 | 0.650 / 0.650 |
| 0.15 | -3 | 7 / 64000 | 7 / 64000 | True | 3.295 / 3.295 | 0.282 / 0.282 |
| 0.15 | 1 | 0 / 64000 | not in srch15 | - | - | - |

### Noise-only packets (R = 0.15)

| SNR | receiver | packets | accepted packets (false alarms) | accepted decodes | 95 % upper bound | CRC passes / caught by re-encoding | total [M] | per core [M] | crit_par_h [M] | per core 99 % / max [M] | dec/pk |
|---|---|---|---|---|---|---|---|---|---|---|---|
| -1 | S blind final v2 [noise only] | 11200 | 0 | 0 | < 2.7e-04 | 2190 / 2190 | 237.171 | 33.929 | 33.876 | 39.8 / 44.7 | 816.3 |
| -1 | T nph15 [noise only] | 11200 | 0 | 0 | < 2.7e-04 | 2087 / 2087 | 288.389 | 35.057 | 35.000 | 39.8 / 44.7 | 817.8 |
| 0 | S blind final v2 [noise only] | 11200 | 0 | 0 | < 2.7e-04 | 2041 / 2041 | 237.202 | 33.933 | 33.880 | 39.8 / 44.7 | 816.4 |
| 0 | T nph15 [noise only] | 11200 | 0 | 0 | < 2.7e-04 | 1892 / 1892 | 288.627 | 35.086 | 35.030 | 39.8 / 44.7 | 818.5 |

- noise-only -1 dB, T nph15 [noise only] vs base: total +21.6 +- 0.2 %, per core +3.3 +- 0.2 %

- noise-only 0 dB, T nph15 [noise only] vs base: total +21.7 +- 0.2 %, per core +3.4 +- 0.2 %

## Predictions vs results

| prediction | measured | verdict |
|---|---|---|
| S1 nofast, 1/10 -5 ... -1 dB: per core -25 to -35 % | -30.5 / -36.6 / -38.0 / -37.1 % at -5 / -4 / -3 / -1 dB | partial: inside at -5 dB, 2 to 3 points more saving than the range at -4, -3, -1 dB |
| S1, 1/10 -5 ... -1 dB: total -8 to -15 % | -12.1 / -16.8 / -18.1 / -18.2 % | partial: inside at -5 dB, 2 to 3 points more saving elsewhere |
| S1, 1/10 0 dB: per core -15 to -30 %, total -5 to +8 % | per core -29.7 %, total -9.4 % | partial: per core hit (at the edge); total miss (more saving; decodes per packet 2.22 -> 1.10) |
| S1, 0.15 -4 dB: per core -12 to -16 %, total ~-5 % | per core -15.2 +- 0.6 %, total -6.5 % | hit |
| S1, 0.15 -3 / -1 dB: per core -25 to -35 %, total -10 to -14 % | -3 dB: -34.9 % / -14.7 %; -1 dB (nofast_nph4 vs nph4): -35.2 % / -12.2 % | hit within 1 point (-1 dB is not the baseline receiver) |
| S1: BLER unchanged | 8 vs 8 (1/10 -5), 275 vs 273 (0.15 -4), 7 vs 7 (0.15 -3), 0 vs 0 at the 7 other points (64k each) | hit: +2 / 64000 at 0.15 -4 dB is far inside the noise (273: CI 3.8e-3 to 4.8e-3); the 0-error points only bound BLER < 4.7e-5 |
| S1b: crit_par_h vs crit_par -8 to -18 % at 1/10 -5 dB, crit_grid -20 to -40 % | baseline -11.4 %, grid part -24.6 % (nofast: -16.5 %, nofast_spec -17.7 %) | hit |
| S1b: "less elsewhere" | baseline: -12.5 / -12.6 % at 1/10 -4 / -3 dB, -10.6 / -8.7 % at -1 / 0 dB; 0.15: -6.4 % at -4 dB, -12.5 % at -3 dB, -4.9 % at +1 dB | partial: not less at 1/10 -4, -3 dB and 0.15 -3 dB; less at 1/10 -1, 0 dB and 0.15 -4, +1 dB |
| S2 nofast_spec vs nofast, 1/10 -5 dB: total -12 to -16 %, per core -1 to -4 % | total -18.0 +- 0.4 %, per core -10.0 +- 0.3 % | miss (both save more than predicted) |
| S2, 0.15 -4 dB: total -6 to -9 %, per core -1 to -3 % | total -9.3 +- 0.3 %, per core -4.0 +- 0.3 % | partial: both just outside the range (more saving) |
| S2, 1/10 -4 / 0.15 -3 dB: total 0 to -3 %, per core 0 to +2 % | total -5.8 / -7.0 %, per core -1.2 / -2.1 % | miss (a saving where no change or a small cost was predicted) |
| S2: decodes per packet +0.1 to +0.3 | +0.16 / +0.14 / +0.11 / +0.14 | hit |
| S2: BLER unchanged | 9 vs 8 at 1/10 -5 dB, 0 vs 0, 275 vs 275, 7 vs 7 | partial: the count is inside the noise, but the extra error is an UNDETECTED one (finding 3) |
| S3 nph15: noise-only false alarms 0 / 10k in both arms at -1 and 0 dB | 0 / 11200 in both arms at both SNRs | hit |
| S3: +1 dB total +5 to +12 %, per core within +-3 %, 0 errors in both | total +10.1 +- 0.4 %, per core +2.1 +- 0.2 %, 0 / 64000 in both | hit |

## Findings

1. **Skipping the fast-path decode (nofast) cuts MACs per core by 30 to 38 % at R = 1/10 from -5 to 0 dB with the
   same error counts.** Per core 0.310 -> 0.216 M at -5 dB, 0.258 -> 0.163 M at -4 dB, 0.243 -> 0.150 M at -3 dB,
   0.202 -> 0.127 M at -1 dB, 0.153 -> 0.108 M at 0 dB (64 000 paired packets each; the 95 % half-width of the
   relative change from the paired chunks is <= 0.4 points). Total -12.1 / -16.8 / -18.1 / -18.2 / -9.4 %. Errors
   8 vs 8 at -5 dB, 0 vs 0 elsewhere (each 0-error point: BLER < 4.7e-5, 95 %). At R = 0.15: -15.2 % per core at -4 dB
   (0.650 -> 0.551 M, 275 vs 273 errors), -34.9 % at -3 dB (0.282 -> 0.183 M, 7 vs 7). The per-core tail does not
   move at the points with failures: the maximum stays in the 35 to 40 M bin and the 99 % point at 0.15 -4 dB is
   8.9 M in all three receivers.
2. **Where nofast stops paying (task 4): not reached per core in the measured range; reached in total MACs at
   R = 0.15 between -1 and 0 dB (nph4 arms).** The per-core saving shrinks only from its maximum of -38 % (1/10 -3 dB)
   to -29.7 % at 1/10 0 dB and -26.0 % at 0.15 0 dB, where the fast path of the reference arm already accepts 42.6 % /
   41.6 % of the packets. The total saving shrinks faster: 1/10 -18.2 % at -1 dB -> -9.4 % at 0 dB; 0.15
   (nofast_nph4 vs nph4) -12.2 % at -1 dB -> +3.1 +- 0.3 % at 0 dB (1.767 -> 1.821 M). BLER: 0 errors in both arms at
   every point from -4 dB (1/10) and -1 dB (0.15) up. No nofast data above 0 dB (at 0.15 +1 dB the fast path of the
   baseline accepts 77.9 %), and none against the baseline receiver at 0.15 above -3 dB.
3. **The speculative decode (nofast_spec) saves more than predicted, and produced the only undetected error of the S
   runs.** vs nofast: total -18.0 % and per core -10.0 % at 1/10 -5 dB (2.978 M, 0.194 M), -9.3 % / -4.0 % at 0.15
   -4 dB, -5.8 % / -1.2 % at 1/10 -4 dB, -7.0 % / -2.1 % at 0.15 -3 dB. 0.23 to 0.43 speculative decodes per packet,
   41 to 62 % of them accepted. At 1/10 -5 dB it has 9 errors vs 8: the extra one is in a chunk where baseline and
   nofast have 0 errors and it is an accepted wrong decode (undetected = 1 / 64000, 95 % CI 4e-7 to 8.7e-5; the
   baseline and nofast have 0 undetected in all their S points, 512 000 and 448 000 packets). One event: not enough
   to give a rate, enough to say the re-encoding check let a wrong decode through once in the spec arm. Whether
   that decode was a speculative one is not stored.
4. **Per-hypothesis core scheduling (crit_par_h) is worth 5 to 13 % per core for the baseline and 8 to 21 % under
   nofast** (grid part alone -23 to -38 %). nofast and the scheduling add up: crit_par_h of nofast vs crit_par of the
   baseline is -42.0 % at 1/10 -5 dB (0.310 -> 0.180 M), -49 to -51 % at 1/10 -4 ... -1 dB and 0.15 -3 dB, -21.6 % at
   0.15 -4 dB. Measurement-only counter: decisions, BLER and total MACs are identical by construction.
5. **nph15 (4 phases at R = 0.15): no false alarm, cost as predicted.** Noise only: 0 accepted decodes in 11 200
   packets per arm at each of -1 and 0 dB (< 2.7e-4 each, 95 %; pooled 0 / 22 400 per arm, < 1.3e-4). About 0.17 to
   0.20 CRC passes per noise-only packet, all rejected by the re-encoding check (baseline 2190 / 2041, nph15
   2087 / 1892). A noise-only packet costs 237 M total / 33.9 M per core in the baseline and 288 M / 35.1 M with
   nph15 (+21.6 % total, +3.3 % per core; ~817 decodes per packet in both). Signal at +1 dB: 0 / 64 000 errors in
   both, total 0.884 -> 0.973 M (+10.1 %), per core 0.099 -> 0.101 M (+2.1 %).
6. **Against the 128-pilot receivers (4 decodes at once, `est3/plots.pilot_macs`) the gap per core stays about 3 to 8x.**
   1/10 -5 dB: nofast 0.216 M (crit_par_h 0.180 M) vs ML direct 0.068 M and joint ML 0.072 M; 1/10 0 dB: 0.108 M vs
   0.034 / 0.036 M; 0.15 -4 dB: 0.551 M vs 0.069 / 0.073 M; 0.15 -3 dB: 0.183 M vs 0.058 / 0.060 M. Total at 1/10
   -5 dB: nofast 3.63 M, nofast_spec 2.98 M vs 1.75 / 1.87 M.

## Too few errors to support a BLER claim

- R = 1/10: only -5 dB has errors (8 or 9 in 64 000: CI 5e-5 to 2.7e-4, a factor 5 wide). -4 to 0 dB: 0 / 64 000 in
  every receiver, only BLER < 4.7e-5.
- R = 0.15: -4 dB is solid (273 to 275 errors); -3 dB has 7 errors per receiver; -1, 0, +1 dB have 0 / 64 000. The
  96 / 520k failures of the baseline at -1 dB seen earlier (1.8e-4) would give ~12 in 64 000: the nph4 arms show 0,
  the baseline receiver itself was not run at -1 dB in S.
- Undetected errors: 1 event in total (finding 3).

## Open questions

- Is the nofast_spec undetected error at 1/10 -5 dB a property of the speculative decode (T = 1, z between 4 and 6)
  or a 1-in-64 000 coincidence? One event; the packet cannot be identified from the stored counters.
- Per core, nofast still saves 26 to 30 % at 0 dB with a 42 % fast-path share; the SNR where it turns into a cost is
  above the measured range.
- 0.15 -4 dB gains much less from nofast (-15 % per core) than every other point (-30 to -38 %). Consistent with,
  not proven by, the counters: the mean there is carried by late / failed packets (99 % point 8.9 M per core, 8.2
  decodes per packet), which nofast does not touch.
- nofast vs the baseline receiver at R = 0.15, -1 and 0 dB was not measured (only on top of nph4).

## Plots (`BLIND_IMPLEMENTATION/testing/results/plots/`)

- `s_bler_R1_10.png`, `s_bler_R0.15.png`: BLER vs SNR per receiver (95 % intervals; 0-error points not drawn, counts in the legend)
- `s_macs_R1_10.png`, `s_macs_R0.15.png`: MACs per core vs SNR (dashed: crit_par_h; dotted: ML direct / joint ML, 128 pilots, 4 decodes at once)
- `s_macs_total_R1_10.png`, `s_macs_total_R0.15.png`: total MACs vs SNR
- `s_noise_R0.15.png`: noise-only CRC passes (all rejected), false-alarm counts and MACs, baseline vs nph15

Lines are broken where two measured SNRs are more than 2 dB apart (no interpolation across unmeasured points).
