# Full-system results after joint tuning (2026-11-18)

Blind receiver (no preamble, no pilots, blind CFO and phase, polar CA-SCL with CRC-32) against two deployed systems
that send known symbols: DVB-RCS2 (waveform IDs 3, 13, 14, 42) and VDE-SAT Link 32. Same payload, CFO range +-0.03 of
the symbol rate, timing known, full Tx/Rx chain. Eb/N0 is per payload bit with the competitor's known-symbol energy
charged. MACs are per core per packet on the 32-core scheduled model; the competitor counts its own synchroniser and
decoder in the same unit. Details: [fullsys/README.md](../../../fullsys/README.md); tuning evidence:
[tuning_fullsys.md](tuning_fullsys.md).

## Headline

| System | Eb/N0 at BLER 1e-3: competitor / blind | Blind lead | Mean MACs per core near BLER 1e-3: blind / competitor |
|---|---|---|---|
| DVB-RCS2 ID 13 | 1.62 / 1.33 dB | **+0.29 dB** | 0.79 / 0.175 M (4.5x) |
| DVB-RCS2 ID 42 | 1.58 / 1.28 dB | **+0.29 dB** | 0.12 / 0.185 M (blind cheaper) |
| DVB-RCS2 ID 3 | 2.88 / 2.30 dB | **+0.58 dB** | 0.16 / 0.055 M (2.9x) |
| DVB-RCS2 ID 14 | 2.01 / 1.76 dB | **+0.24 dB** | 0.17 / 0.26 M (blind cheaper) |
| VDE-SAT Link 32 | 2.93 / 1.78 dB | **+1.15 dB** | 0.21-0.23 / 0.028 M (~8x) |

## What the joint tuning changed
- **VDE-SAT:** jointly tuned (batch null on 32 cores, final 4, win 4.0, shortlist 99.7 %/4) plus ONE phase guess instead of two: same BLER (paired fresh packets), mean MACs per core 5.88 -> 2.05 M at -6.6 dB and 0.42 -> 0.21 M at -4.6 dB (-50 ... -65 %), worst case 8.4 -> 2.9 M.
- **DVB-RCS2:** BLER unchanged on all four IDs; MACs lower only in the waterfall (ID 14 -46 ... -23 %, ID 42 -14 ... -7 %),
  ~0 % at the operating point; ID 3 +1 ... +9 % for a few fewer errors. The DVB receivers had little slack left (no
  block schedule to remove, F5 already tuned).

## How it was tuned
- Calibration packets only (seeds disjoint from every test run), the 2 % rule at every calibration point, then a live
  check on the same calibration packets, a held-out log (VDE) and the final curve on fresh test packets paired with
  the receiver before tuning.
- VDE: offline joint tuner replaying a full-search log (self-check exact on 50k packets; live check matched the
  replay to 0.002 M per core). DVB: live combinations (its joint list decodes cannot be replayed).
- Rejected with evidence: MAC caps (not needed: worst case 2.9 M), F5 on VDE (~2 % for extra risk), coarser
  CFO grid (2-4x the errors), NN checkpoint position (no gain), the first tuner pick (cheap only at low SNR).

## Plots
- VDE: [fs_vde32_final.png](plots/VDE-SAT/overview/fs_vde32_final.png),
  [fs_vde_macs_vs_snr.png](plots/VDE-SAT/MACs/fs_vde_macs_vs_snr.png),
  [fs_vde_tuned_capped.png](plots/VDE-SAT/MACs/fs_vde_tuned_capped.png),
  [fs_vde_tuned_macs_capped.png](plots/VDE-SAT/MACs/fs_vde_tuned_macs_capped.png).
- DVB-RCS2: [fs_tuned_id13.png](plots/DVB-RCS2/overview/fs_tuned_id13.png),
  [fs_tuned_id42b.png](plots/DVB-RCS2/overview/fs_tuned_id42b.png),
  [fs_tuned_id3.png](plots/DVB-RCS2/overview/fs_tuned_id3.png),
  [fs_tuned_id14s.png](plots/DVB-RCS2/overview/fs_tuned_id14s.png).

## Open / next
- VDE retune around one phase guess (fs-jtv32n): joint tuner rerun on one-phase logs picked final 0 + ck_min 8 + tau 0 + final_post 32 + ncand 1 (replay -23 % vs its base); not adopted tonight (final 0 needs a live check, it failed at high SNR before).
- NB-IoT NTN, then phase 2 (SS-TC-LM).
- Local disk C: is nearly full (1.7 GB free); free space before the next large pulls.
