# Online tests: list-marginalised re-ranking (F3) and DD-Newton refinement (TODO 3), predictions 2026-11-15, before code
Sources: expected_f3f5.md (F3 measured: P(true cell top 4) 0.9744 -> 0.9947 / 0.9989 with L_e 2 / 8 at 0.15 -4 dB),
expected_ref.md (D0: DD Newton from the centre codeword 2-3x more accurate than the grid at ~1/4 of its MACs at 1/10,
0.15). Baseline = testing_s11g (1/10, 0.15), paired on the same packets. No point below -5 dB.

## A. `lm2` / `lm4`: re-rank the last-checkpoint survivors by the list-marginalised metric (L_e = 2 / 4)
At the last checkpoint (c = 3/4), every surviving (cell, phase) hypothesis is decoded to c = 3/4 with an SC list of
L_e paths (Fast-SSCL as in lit_checks lmarg), metric = -logsumexp(-PM); the candidate order (z > 4 candidates, then the
best 32) uses that metric instead of the list-1 PM. Everything else unchanged.
| Point | BLER base -> lm2 | per core |
|---|---|---|
| 0.15 -4 dB | 4.1e-3 -> 2.5e-3 ... 3.5e-3 (Stage-2 misses fixed, ~60 % of failures are Stage 2) | +10 ... +40 % (L_e x the survivors' decode to 3/4) |
| 0.15 -3.5 dB | 7e-4 -> 5e-4 ... 7e-4 | +10 ... +30 % |
| 1/10 -5 dB | 1.6e-4 -> 1.2e-4 ... 1.6e-4 | +10 ... +30 % |
- Kill: BLER not lower at 0.15 -4 dB (paired p < 0.05 needed for a claim) or undetected > base + 2.
## B. `ddref`: DD-Newton refinement replacing the grid at 1/10, 0.15
For each candidate cell: list-1 SC codeword at the cell centre -> z = r' s^* -> 2 Newton steps -> f, theta; score
{f} x {theta, theta +- pi/12 when 4 phases} by the list-1 metric, decode the best T = 2 (as the grid); if none passes,
fall back to the existing grid refinement of that cell.
| Point | BLER base -> ddref | total MACs | per core |
|---|---|---|---|
| 1/10 -5, 0.15 -4 / -3.5 / -3 dB | same (within +-10 %), maybe lower at 0.15 -4 dB (37 % of failures were lost in Stage 3) | -5 ... -14 % | -5 ... +5 % (DD is serial; the grid ran in parallel) |
- Kill: BLER loss (paired p < 0.05) or undetected > base + 2, or total saving < 3 %.

## Code review (2026-11-15): GO with fixes — cost predictions revised
- Baseline with flags off bit-identical; lmarg / ddref logic correct; acceptance unchanged.
- lmarg cost (verifier's count, ~120 surviving hypotheses at 0.15 -4 dB): per core L2 +0.14 M (+35 %), L4 +0.27 M (+66 %),
  not +10...40 %. A top-K-by-list-1 cut would drop exactly the gained packets (12 of 40 have list-1 rank > 32).
  New arm `lm2z` (lazy: list re-ranking only when the first candidate fails, ~10-15 % of packets): predicted
  +5 % per core or even net negative (fewer Stage-3 sweeps), keeping most of the rank gain.
- ddref: correct, but on wrong cells it always falls back to the grid -> predicted total +20...25 %, per core up,
  i.e. likely KILL. New arm `ddref_s2` (only win / spec / s2cand, T_dd = 1, codeword reused): ~break-even. Both ddref
  arms only in the smoke; they go into the full runs only if the smoke shows total MACs <= base.
- Smoke now at 0.15 -4 and -5 dB with 6 arms; full runs onl15a/b, onl10 with base, lm2, lm2z, lm4.

## Measured: onl15b, 0.15 -3.5 dB, 64k packets paired (2026-11-15 20:28, ALL DONE, no Traceback)
| Arm | errors | n10 / n01 vs base | undetected | per core (crit_par_h_d4a) | lm runs per packet |
|---|---|---|---|---|---|
| base testing_s11g | 48 (7.5e-4) | - | 0 | 0.226 M | - |
| lm2 | 51 | 1 / 4 | 0 | 0.224 M | 0.8 % |
| lm2z | 51 | 1 / 4 | 0 | 0.224 M | 0.5 % |
| lm4 | 50 | 1 / 3 | 0 | 0.225 M | 0.8 % |
- No gain at -3.5 dB (predicted 7e-4 -> 5e-4 ... 7e-4): the list re-ranking runs in < 1 % of packets here and changes
  ~5 outcomes, net +2 to +3 errors (not significant). Cost also ~0 (-1 %), since it rarely runs. The decisive point
  is 0.15 -4 dB (onl15a, still running), where 60 % of the failures were Stage 2.

## Measured: onl15a, 0.15 -4 dB, 64k packets paired (2026-11-15 20:37, ALL DONE, no Traceback)
| Arm | errors | n10 / n01 vs base | undetected | per core (crit_par_h_d4a) | total MACs | lm runs per packet |
|---|---|---|---|---|---|---|
| base testing_s11g | 245 (3.8e-3) | - | 1 | 0.391 M | 7.21 M | - |
| lm2 | 241 | 11 / 7 | 1 | 0.366 M (-6.4 %) | 7.08 M | 5.2 % |
| lm2z | 241 | 11 / 7 | 1 | 0.365 M (-6.6 %) | 7.03 M | 4.5 % |
| lm4 | 241 | 11 / 7 | 1 | 0.370 M (-5.4 %) | 7.27 M | 4.9 % |
- **BLER: kill rule A met.** Predicted 4.1e-3 -> 2.5e-3 ... 3.5e-3; measured 3.83e-3 -> 3.77e-3, McNemar p = 0.48
  (not significant). The offline F3 rank gain (P(true cell top 4) 0.974 -> 0.995) does not turn into decodes: most
  rescued ranks were packets the baseline already decoded later in Stage 3.
- **Unexpected: per core -6 %** at -4 dB (cost predicted +5 % for lm2z, +35 % for lm2): the better order reaches the
  right candidate earlier, so fewer Stage-3 sweeps. At -3.5 dB only -1 %. Logged in DEAD_ENDS.md as a BLER idea;
  kept open as a MAC trim pending onl10 (1/10 -5 dB).

## Measured: onl10, 1/10 -5 dB, 64k paired (2026-11-15 20:54, ALL DONE, no Traceback)
| Arm | errors | n10 / n01 | undetected | per core | lm runs per packet |
|---|---|---|---|---|---|
| base | 18 | - | 0 | 0.2088 M | - |
| lm2 | 18 | 0 / 0 | 0 | 0.2076 M (-0.6 %) | 0.6 % |
| lm2z | 18 | 0 / 0 | 0 | 0.2074 M (-0.7 %) | 0.5 % |
| lm4 | 18 | 0 / 0 | 0 | 0.2082 M (-0.3 %) | 0.6 % |
- Predicted 1.6e-4 -> 1.2e-4 ... 1.6e-4: no change. MAC trim at 1/10: -0.7 %, negligible.
- **Verdict:** lm2z is a MAC trim only where Stage 2 fails often (0.15 -4 dB: -6.6 %; -3.5 dB: -1 %; 1/10 -5 dB:
  -0.7 %). At the 0.15 1e-3 operating point (-3.6 dB) that is ~-2 %. Not adopted (DEAD_ENDS.md).
