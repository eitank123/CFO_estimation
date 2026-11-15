# The adopted testing receiver (`testing_spec11`) over the SNR range: predictions, written 2026-11-13 before any result

Arms: `testing` (nph 4 phases below 0.5 dB at 0.15, q_fix, fast path off at <= 0 dB) vs `testing_spec11` (+ speculative
decode at 4 < z <= 6, accepted at rho > 1.1 thr). Same packets. 64k per SNR (16 chunks x 4000).
Jobs s11-10a (1/10 -5, -4.5, -4), s11-10b (1/10 -3, -2, -1, 0), s11-15a (0.15 -4, -3.5, -3, -2.5), s11-15b (0.15 -2, -1,
0, +1). Purpose: the MAC curves of the adopted receiver for the cmp_* plots (BLER stays the big-sample testing curve).

## Predictions
- BLER: identical to `testing` packet for packet at every SNR (0 ... 2 discordant per point); undetected 0 ... 1 per point.
- Per core (scheduled): 1/10 -5 dB -13 ... -16 %, -4.5 / -4 dB -8 ... -15 %, -3 ... 0 dB -2 ... -8 % (fewer packets end in the
  4 < z <= 6 band as the SNR rises: most win at z > 6 in round 1). 0.15 -4 dB -5 ... -9 %, -3.5 ... -2.5 dB -3 ... -6 %, -2 ... 0
  dB -1 ... -5 %; +1 dB (fast path on, 2 phases) 0 ... -3 % (the fast path decides most packets before Stage 3).
- Total: about 1.3x the per-core change (as on 1/10 -5 dB: -19.4 % total vs -14.5 % per core).
- Kill: any point with > 3 broken packets, or undetected > base + 1, or per core higher than base by > 1 %.

## Smoke (s11-smoke): 0.15 -4.5 dB (high BLER) and 0.15 +1 dB (fast path on: the only untested combination), 1600 packets
per point, both arms. Pass: EVAL DONE + ALL DONE, no Traceback, discordant <= 2, at +1 dB per core within -5 ... +1 %.

### Smoke result (2026-11-13)
EVAL DONE + ALL DONE, no Traceback. 0.15 -4.5 dB: 49 vs 49 errors, 0 discordant, undetected 0 / 0, per core -2.1 %, total
-3.5 %. 0.15 +1 dB: 0 / 0 errors, per core +0.4 % (inside -5 ... +1 %), total -0.1 %. PASS: s11-10a/b, s11-15a/b submitted.

## Measured (s11-10a/b, s11-15a/b, 64k paired per SNR; all EVAL DONE + ALL DONE, no Traceback; 2026-11-14)
| R | SNR | errors (both arms) | undetected | per core testing -> spec11 | total |
|---|---|---|---|---|---|
| 1/10 | -5 | 10 | 1 / 1 | 0.241 -> 0.206 M (-14.6 %) | -19.5 % |
| 1/10 | -4.5 | 1 | 0 | -10.1 % | -15.0 % |
| 1/10 | -4 | 1 | 0 | -3.6 % | -7.4 % |
| 1/10 | -3 | 0 | 0 | +3.7 % | +1.7 % |
| 1/10 | -2 / -1 / 0 | 0 | 0 | +4.3 / +3.3 / +2.7 % | +2.6 / -0.3 / +0.5 % |
| 0.15 | -4 | 260 | 0 | -7.0 % | -10.3 % |
| 0.15 | -3.5 | 45 | 0 | -8.1 % | -12.2 % |
| 0.15 | -3 | 7 | 0 | -4.1 % | -7.9 % |
| 0.15 | -2.5 | 1 | 0 | +0.5 % | -2.3 % |
| 0.15 | -2 / -1 / 0 | 0 | 0 | +3.0 / +3.6 / +2.8 % | +1.1 / +2.2 / +1.7 % |
| 0.15 | +1 | 0 | 0 | +0.5 % | -0.3 % |
0 discordant packets at every point.
- vs predictions: BLER identical: HIT. 1/10 -5, -4.5 dB and 0.15 -4 ... -3 dB savings: HIT. 1/10 -4 dB -3.6 % (predicted -8 ...
  -15 %): MISS (low). Above the waterfall predicted -1 ... -8 %, measured +3 ... +4 % per core: MISS, and the kill rule
  (per core > base + 1 %) fires at 1/10 -3 ... 0 dB and 0.15 -2 ... 0 dB. Reason: once most packets win in round 1 the
  speculative decode is mostly an EXTRA decode on a cell that the next round would have confirmed anyway.
- Decision: spec11 only in the waterfall. New option small_rx `spec_snr` (win_spec off at SNR >= the per-rate value);
  run.py `testing_s11g` = spec11 below 1/10 -3.5 dB and 0.15 -2.5 dB, `testing` above. At every SNR it is one of the two
  measured arms, so its curves are these numbers piecewise. Smoke s11g-smoke checks the equality (packet for packet and
  MACs) at 1/10 -5 / -3 dB and 0.15 -3 / -2 dB.

### Smoke s11g-smoke (800 packets per point, 2026-11-14)
EVAL DONE + ALL DONE, no Traceback. `testing_s11g` = `testing_spec11` packet for packet and MAC for MAC at 1/10 -5 dB and
0.15 -3 dB, = `testing` at 1/10 -3 dB and 0.15 -2 dB. PASS. **`testing_s11g` is the adopted testing receiver** (1/10, 0.15);
its MAC curves (`agg_cmp.adopted`, pink in `cmp_macs_*`) are the s11 sweep taken piecewise.
