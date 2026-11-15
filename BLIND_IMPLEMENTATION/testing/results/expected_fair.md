# Fair 128-pilot references (jobs fair15, fair10, fair25, fair2): predictions, 2026-11-13, before any result

## Why
The 128-pilot receivers (est3) have a BLER floor of ~2e-5 at R = 0.15 / 1/10 from -2.5 dB up that the blind receiver
does not have. Measured: the floor is almost all undetected errors (ML direct 0.15 -1 dB: 34 errors, 34 undetected).
Cause: their CRC search decodes the estimate and then neighbouring CFOs in a FIXED order (2-5 CA-SCL-8 decodes per
packet); each wrong decode can pass the CRC (3-6e-4 wrong passes per packet), the re-encoding check catches ~93-95 %, the
rest is the floor. Even the CRB-limited receiver has it; the genie (one decode at the true CFO) has 0.

## What is tested
New sources "ML direct PM", "M&M PM" (est3/run_bler.py): the same estimate, then every candidate f_hat + k STEP
(k = 0, +-1 ... +-M, as before) is scored by the list-1 Fast-SSC path metric (in parallel), and CA-SCL-8 decodes the
best PM_T = 3 in metric order, stopping at the first accepted pass (the blind receiver's principle). Same packets as the
fixed-order "ML direct", "M&M" in the same run (new seeds), same acceptance check. MACs: + the metric passes (total
m_evals x (metric + LLR + gain); per core ceil(m_evals / 32) passes).

## Predictions (480k packets per SNR)
| Rate, SNR | fixed order | metric order (PM) |
|---|---|---|
| 0.15 / 1/10, from -2 dB up | floor ~1-3e-5, nearly all undetected | floor gone or x5-10 lower (< 5e-6 ... 5e-6), undetected <= 2 per 480k |
| 0.15 -4 / -3 dB, 1/10 -5 / -4 dB (waterfall) | as before | BLER within +-20 % (same estimate; capped at 3 decodes it may lose a few late finds) |
| 2/5, 1/2 | as before | about the same BLER; undetected lower |
| decodes per packet | 2-5.5 at low SNR | 1.0-1.3 |
| MACs per core | as before | +-15 % (fewer decodes, plus one parallel metric pass) |
Consequence: the pilot curves in cmp_bler_R*.png and the cap plots get the "PM" versions as the fair reference; the
blind-vs-pilots verdict at 0.15 / 1/10 above -2.5 dB is re-evaluated.

## Measured (fair15, fair10, fair25, fair2; 480k packets per SNR and source, 2026-11-13)
All 4 logs EVAL DONE + ALL DONE, no Traceback. Errors / 480k (undetected in brackets); per core from est3
`plots.pilot_macs` (4 decodes at once + the metric passes).
| Rate, SNR | Genie | ML direct (fixed) | ML direct PM | M&M (fixed) | M&M PM | per core ML fixed -> PM |
|---|---|---|---|---|---|---|
| 0.15 -4 | 524 | 559 (27) | 2067 (2) | 683 (20) | 2245 (1) | 0.069 -> 0.085 M |
| 0.15 -3 | 0 | 24 (24) | 10 (0) | 23 (18) | 15 (0) | 0.057 -> 0.084 M |
| 0.15 -2 | 0 | 12 (12) | 0 | 14 (14) | 0 | 0.049 -> 0.083 M |
| 0.15 -1 | 0 | 9 (9) | 0 | 7 (7) | 0 | 0.043 -> 0.082 M |
| 0.15 0 | 0 | 4 (4) | 0 | 5 (5) | 0 | 0.038 -> 0.081 M |
| 0.15 +1 | 0 | 5 (5) | 0 | 4 (4) | 0 | 0.035 -> 0.080 M |
| 1/10 -5 | 12 | 33 (22) | 150 (0) | 1677 (17) | 1784 (0) | 0.068 -> 0.102 M |
| 1/10 -4 | 0 | 12 (12) | 0 | 169 (12) | 157 (0) | 0.057 -> 0.080 M |
| 1/10 -3 ... 0 | 0 | 13 / 10 / 9 / 5 (all und.) | 0 | 19 / 7 / 8 / 5 | 3 / 1 / 0 / 0 | 0.049 ... 0.034 -> 0.079 ... 0.076 M |
| 2/5 0.5 | 1229 | 1223 (18) | 3643 (1) | 1228 (23) | 3665 (0) | 0.062 -> 0.095 M |
| 2/5 1.0 | 20 | 36 (12) | 144 (0) | 33 (11) | 127 (0) | 0.056 -> 0.094 M |
| 2/5 1.5 / 2.0 | 0 / 0 | 7 / 5 (all und.) | 0 / 0 | 10 / 3 | 2 / 0 | 0.052 / 0.049 -> 0.094 / 0.067 M |
| 1/2 2.0 | 134 | 150 (14) | 431 (0) | 150 (11) | 435 (1) | 0.059 -> 0.069 M |
| 1/2 2.5 / 3.0 | 2 / 0 | 11 / 10 | 6 / 0 | 10 / 3 | 5 / 0 | 0.054 / 0.051 -> 0.069 M |

vs predictions:
- Floor: HIT. Above the waterfall the PM versions have 0 errors (0.15 from -2 dB, 1/10 from -1 / -4 dB, 2/5 2 dB,
  1/2 3 dB) and 0-2 undetected per point everywhere (fixed order: 3-27 undetected per point). Wrong CRC passes fall
  from 66-444 to 0-4 per 480k.
- Waterfall BLER: MISS. PM is x3-4 worse at 0.15 -4, 2/5 0.5 / 1.0, 1/2 2.0, x4.5 at 1/10 -5 (ML direct). Cause: the
  list-1 metric at low SNR does not always rank f_hat (or the right neighbour) in its top 3, and PM never decodes at
  f_hat then; the fixed order always decodes f_hat first and then tries ~6 neighbours.
- MACs per core: MISS (predicted +-15 %): +20 ... +130 % (the 35-69 metric passes for EVERY packet = 2-3 metric rounds
  on 32 cores, more than the 1-6 extra decodes they save at 4 at once).
- Conclusion: neither search is the fair reference on its own. Next: PM+T (below).

## PM+3, PM+all (jobs fairb-smoke, fairb15, fairb10, fairb25, fairb2): predictions, written before any result
" PM+T": decode at f_hat first (exactly as the fixed order); only for packets it does not accept, score the 2M
neighbours by the list-1 metric (KP = 32 at a time; MACs charged per such packet: metric_rounds) and decode at most T of
them in metric order (T = 3, or all 2M), stopping at the first accepted pass. Same packets as a new fixed-order run
(seeds 37-40, 480k per SNR).
| | PM+all | PM+3 |
|---|---|---|
| waterfall BLER (0.15 -4, 1/10 -5, 2/5 0.5, 1/2 2) | = fixed +-10 % (same hypotheses; only the order differs) | fixed ... +30 % (a few late finds lost) |
| BLER above the waterfall | 0 ... 1e-5: the floor x3-10 lower than fixed (the right neighbour is tried first, so fewer wrong decodes before it) | 0 ... 5e-6 |
| undetected per point | fewer than fixed (x2-5) | 0-3 |
| per core vs fixed | +0 ... +40 % at low SNR (metric rounds for the ~50 % failing packets), +10 ... +30 % high SNR | about PM+all or lower |
- If PM+all keeps the fixed-order BLER and removes most of the floor, it becomes the fair pilot reference in the
  cmp_* and cap plots (with the fixed order kept as a thin line). If PM+3 matches PM+all in BLER, PM+3 instead (cheaper).
- Smoke (fairb-smoke, 0.15 -4 dB, 1600 packets): checks that the code runs, PM+all within a few errors of fixed, PM+3
  >= PM+all, metric_rounds > 0.

### Smoke (fairb-smoke, 0.15 -4 dB, 1600 packets, 2026-11-13)
EVAL DONE + ALL DONE, no Traceback. Errors: fixed 0 / 0 (ML direct / M&M), PM+all 0 / 0, PM+3 6 / 4; extra decodes per
packet fixed 6.13 / 6.42 -> PM+all 0.78 / 0.80, PM+3 0.73 / 0.74; metric_rounds 2300 / 2356 (= failing packets x 2).
PM+all behaves as predicted; PM+3 already loses packets in the waterfall (expect it to fail the BLER part).

## Measured: PM+3, PM+all (fairb15, fairb2; 480k per SNR, same packets in every source; logs EVAL DONE + ALL DONE, no Traceback)
Errors (undetected), ML direct / M&M; per core (scheduled, 4 decodes at once) in M.
| Point | fixed order | PM+all | PM+3 | per core fixed -> PM+all |
|---|---|---|---|---|
| 0.15 -4 dB | 604 (22) / 734 (13) | 587 (5) / 726 (5) | 1766 (5) / 1901 (5) | 0.069 -> 0.076 (+10 %) |
| 0.15 -3 dB | 11 (10) / 19 (17) | 2 (1) / 3 (1) | 15 / 15 | 0.058 -> 0.067 (+16 %) |
| 0.15 -2 dB | 19 (19) / 12 (12) | 5 (5) / 2 (2) | = PM+all | 0.049 -> 0.060 (+22 %) |
| 0.15 -1 dB | 16 / 9 | 4 / 5 | = PM+all | 0.043 -> 0.054 (+26 %) |
| 0.15 0 dB | 4 / 7 | 2 / 2 | = PM+all | 0.038 -> 0.048 (+26 %) |
| 0.15 +1 dB | 12 / 4 | 6 / 2 | = PM+all | 0.035 -> 0.043 (+23 %) |
| 1/2 2 dB | 176 (13) / 176 (10) | 168 (5) / 170 (4) | 372 / 386 | 0.059 -> 0.063 (+7 %) |
| 1/2 2.5 dB | 11 (9) / 15 (13) | 2 (0) / 8 (6) | 4 / 9 | 0.054 -> 0.059 (+9 %) |
| 1/2 3 dB | 8 / 6 | 3 / 1 | = PM+all | 0.051 -> 0.057 (+11 %) |
Total MACs: PM+all +8 % at 0.15 -4 dB, -2 ... -7 % from -1 dB up (fewer extra decodes: 0.3-0.9 instead of 1-6.6 per packet).
- vs predictions: PM+all waterfall BLER = fixed within -3 ... -5 % (predicted +-10 %): HIT. Floor x2-5 lower (predicted x3-10):
  HIT (low edge); a residual 2-6 per 480k remains, nearly all undetected (wrong codewords that pass CRC-16 + the re-encoding
  check at the first or a metric-chosen neighbour). Undetected x2-4 lower: HIT. Per core +7 ... +26 % (predicted +0 ... +40 %
  low SNR, +10 ... +30 % high): HIT. PM+3: waterfall BLER x2.2-2.9 (predicted <= +30 %): MISS, the true neighbour is often
  ranked 4th or lower by the list-1 metric; above the waterfall it equals PM+all.

### fairb10, fairb25 (480k per SNR)
| Point | fixed order | PM+all | PM+3 | per core fixed -> PM+all |
|---|---|---|---|---|
| 1/10 -5 dB | 23 (17) / 1735 (17) | 11 (5) / 1722 (4) | 108 / 1832 | 0.067 -> 0.083 (+24 %) |
| 1/10 -4 dB | 20 (20) / 157 (13) | 4 (4) / 147 (3) | 4 / 147 | 0.057 -> 0.063 (+11 %) |
| 1/10 -3 dB | 15 / 26 | 2 / 11 | = PM+all | 0.049 -> 0.057 (+16 %) |
| 1/10 -2 ... 0 dB | 8-11 / 6-17 per point | 1-5 / 0-6 | = PM+all | +18 ... +24 % |
| 2/5 0.5 dB | 1197 (20) / 1215 (16) | 1183 (6) / 1205 (6) | 3075 / 3105 | 0.062 -> 0.083 (+34 %) |
| 2/5 1 dB | 41 (11) / 33 (8) | 33 (3) / 27 (2) | 106 / 103 | 0.056 -> 0.076 (+36 %) |
| 2/5 1.5 dB | 12 / 10 | 7 / 4 | 9 / 7 | 0.052 -> 0.056 (+8 %) |
| 2/5 2 dB | 9 / 9 | 5 / 6 | = PM+all | 0.049 -> 0.053 (+8 %) |
- Same picture at all four rates: PM+all = fixed in the waterfall (-1 ... -2 %; at 1/10 -5 dB ML direct 23 -> 11, the fixed
  order's errors there are mostly its floor), floor x2-5 lower, undetected x3-5 lower; per core +8 ... +36 %. Totals within
  -8 ... +15 %. PM+3 x2.5-4.7 in every waterfall. M&M at 1/10 -5 dB (3.6e-3) is its estimator, not the search.
- **Decision: PM+all is the fair pilot reference** (cmp_* and cap plots: ML direct PM+all, M&M PM+all; the fixed-order
  curves stay as thin dotted lines). PM+3 and " PM" are dropped (DEAD_ENDS.md). Joint ML and cnn-cr were not rerun
  with PM+all: they stay as thin fixed-order lines (their floor is the same search artefact).
