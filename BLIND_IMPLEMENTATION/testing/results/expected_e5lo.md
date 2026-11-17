# e5-10lo: the 1/10 competitors that sat at genie level (predictions 2026-11-15, before the run)

**Why:** in e5-10 (R = 1/10, 480k packets per point) three deployed layouts had genie-level BLER at the lowest point,
data Es/N0 = -5 dB: CCSDS style 15 / 480k, DMRS 1/7 8 / 480k, MIL-110 HF 8 / 480k (Genie 17 / 480k). On the fair
axis (pilot energy charged: +0.51 / +0.67 / +1.14 dB) that point is -4.49 / -4.33 / -3.86 dB, so their 1e-4
crossing lies below the simulated range and the comparison with blind (-4.78 dB, CI [-4.86, -4.69], 544k per point)
is open. No code change: est4/run_bler.py as in e5-10, new seeds 71-73, own part per source.

| Part | Source | data Es/N0 [dB] | fair-axis SNR [dB] | packets |
|---|---|---|---|---|
| e5-10lo-a | CCSDS style | -5.5 | -4.99 | 480k |
| e5-10lo-b | DMRS 1/7 | -5.65 | -4.98 | 480k |
| e5-10lo-c | MIL-110 HF | -6.1, -5.5 | -4.96, -4.36 | 480k each |

Every point is >= -5 dB on the plotted axis. Runtime: e5-10 took 16.4 ks for 45 source-points -> ~0.37 ks each ->
~25 min for the 4 here.

## Predicted BLER
Slope from blind and Genie near -5 dB: about x6 per 0.5 dB.

| Part | Point | Predicted BLER (errors in 480k) |
|---|---|---|
| a | CCSDS style -5.5 | 1.2 ... 3e-4 (60-150) |
| b | DMRS 1/7 -5.65 | 1.5 ... 4e-4 (70-200) |
| c | MIL-110 HF -6.1 | 0.8 ... 2e-3 |
| c | MIL-110 HF -5.5 | 0.7 ... 2e-4 |

## Predicted comparison with blind (R = 1/10, BLER 1e-4, fair axis)
Gap = receiver - blind (+ = blind better). MACs per core: blind 0.194 M at its crossing.

| Receiver | Predicted required SNR [dB] | Gap to blind [dB] | Verdict | MACs ratio blind / it |
|---|---|---|---|---|
| CCSDS style | -4.85 ... -4.70 | -0.07 ... +0.08 | tie (within blind's CI) | ~3x (0.065 M) |
| DMRS 1/7 | -4.80 ... -4.65 | -0.02 ... +0.13 | tie, blind slightly better | ~5.5x (0.035 M) |
| MIL-110 HF | -4.35 ... -4.15 | +0.43 ... +0.63 | blind better | ~5.5x (0.035 M) |

Kill / flag rule: if any of the three is still below 1e-4 at its lowest new point, it beats blind at 1/10 by more
than the blind CI; report it as a loss for blind rather than extend below -5 dB (no runs below -5 dB on the plotted axis).

## Measured (2026-11-15 20:16, e5-10lo ALL DONE, no Traceback)
| Part | Point (fair axis) | Predicted | Measured |
|---|---|---|---|
| a | CCSDS style -4.99 | 1.2 ... 3e-4 | **8.6e-4** (414 / 480k): steeper than predicted (x27 per 0.5 dB, not x6) |
| b | DMRS 1/7 -4.98 | 1.5 ... 4e-4 | **1.7e-3** (813 / 480k) |
| c | MIL-110 HF -4.96 | 0.8 ... 2e-3 | **1.3e-2** (6323 / 480k), 48 undetected |
| c | MIL-110 HF -4.36 | 0.7 ... 2e-4 | **5.6e-4** (267 / 480k), 1 undetected |

| Receiver | Required SNR @1e-4 [dB] (95 % CI) | Gap to blind (-4.78) | Predicted gap | Verdict | MACs blind / it |
|---|---|---|---|---|---|
| CCSDS style | -4.66 [-4.72, -4.60] | **+0.12** | -0.07 ... +0.08 | miss: blind slightly better (CIs touch) | 3.0x |
| DMRS 1/7 | -4.58 [-4.65, -4.51] | **+0.20** | -0.02 ... +0.13 | miss: blind better | 5.7x |
| MIL-110 HF | -4.11 [-4.17, -4.05] | **+0.67** | +0.43 ... +0.63 | close miss: blind better | 5.6x |

Why the miss: the genie-level points at -5 dB raw hid how steep their waterfalls are; I extrapolated with blind's
slope. All three predictions erred in the competitors' favour. MIL-110 at -4.96 dB has 48 undetected errors in
480k (1e-4): its CRC search runs at high BLER there.
