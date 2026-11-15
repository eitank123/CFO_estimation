# Literature checks (job lit1, script lit_checks.py), 2026-11-13

## Phase equivariance without the interleaver (Geiselhart et al. 2023): CONFIRMED
Per packet at the true CFO, list-1 SC metric at theta + q pi/2 minus the one at theta (q = 1, 2, 3):
| point | packets | no interleaver: max / mean abs diff | with the interleaver: mean / median abs diff | CA-SCL-8 rotation-aware, right at q = 0 / 1 / 2 / 3 |
|---|---|---|---|---|
| 0.15 -3 dB | 4000 | 1.2e-4 / 4e-8 (float rounding) | 254 / 355 | 4000 / 4000 / 4000 / 4000, 0 wrong |
| 2/5 1 dB | 2000 | 1.2e-4 / 8e-8 | 295 / 417 | 2000 each, 0 wrong |
| 1/10 -5 dB | 2000 | 1.2e-4 / 4e-8 | 174 / 241 | 2000 each, 0 wrong |
-> Without the bit interleaver (no BLER effect in AWGN with Gray QPSK) the pi/2 phase hypotheses are redundant: half the
phases per cell, one fast-path branch; the decoder un-rotates its list paths (4 CRC checks per path). Next: the
receiver option `equiv` (BLIND_NOINT=1), paired runs.

## Frozen-bit ranking of the grid cells (Giard et al. 2017/18): NO GAIN
Rank of the true cell among 201 cells (4 phases each, full-length metric), 2000 packets per point:
| point | P(rank 1) total / frozen-only / no SPC | P(rank <= 4) total / frozen-only / no SPC |
|---|---|---|
| 0.15 -4 dB | 0.857 / 0.858 / 0.859 | 0.9725 / 0.9735 / 0.973 |
| 0.15 -3 dB | 0.911 / 0.9115 / 0.9115 | 1.0 / 1.0 / 1.0 |
| 1/10 -5 dB | 0.895 / 0.897 / 0.897 | 0.998 / 0.9985 / 0.9985 |
-> At these low rates almost every node is rate-0 / REP, so dropping the rest changes nothing. Dropped.
