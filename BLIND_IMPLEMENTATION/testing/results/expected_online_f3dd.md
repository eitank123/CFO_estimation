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
