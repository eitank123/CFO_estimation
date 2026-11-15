# Presentation figures

One figure per rate (R = 1/10, 0.15, 2/5, 1/2; file suffix `R1_10`, `R0.15`, `R2_5`, `R1_2`). SNR axis = Es/N0 in dB, from
-5 dB up.

## Use these for the comparison slides (updated 2026-11-15)

| Files | What it shows | Made by |
|---|---|---|
| `bler_fair_R*.png` | **BLER vs SNR: blind vs every pilot receiver, fair comparison.** The pilots are extra symbols outside the 1024-symbol packet, and their energy is charged on the SNR axis. Receivers: blind (no pilots); DVB-RCS2 pilot layout (ID 13, 116 known symbols, Rife-Boorstyn FFT); 128-symbol preamble with ML; 128-symbol preamble with Mengali-Morelli; 64 + 64 pre/post with joint ML; DVB-RCS2 16 + 16 pre/post with the 4th-power estimator; genie (true CFO and phase, lower bound) | [testing/plot_pres.py](../testing/plot_pres.py) |
| `macs_fair_R*.png` | MACs per core per packet (the standard scheduled 32-core count) of the same receivers vs the same SNR axis | [testing/plot_pres.py](../testing/plot_pres.py) (via `testing/plot_e4.py`) |

How the curves are smoothed (statistics only, no curve fit):
- Blind: all runs of the same receiver are pooled per SNR (64k-1.4M packets per point).
- Pilot receivers: each SNR point has 480k packets. Above the waterfall the 128-preamble receivers have a flat floor of
  wrong CRC passes (1-6 per 480k per point, which made the old curves jitter). Those are pooled over the flat region;
  the legend gives the count, for example "16 in 2.4M packets".

What they show:
| Rate | BLER | MACs per core |
|---|---|---|
| 1/10 | blind best: about 0.2 dB better than the best pilot receiver (128 ML) at BLER 1e-4 | blind 5-6x the DVB-RCS2 receiver |
| 0.15 | a tie: blind 0.15 dB better at 1e-3, 0.14 dB worse at 1e-4 | blind 5-11x |
| 2/5 | blind about 0.5 dB better | blind about 6x at 0.5 dB |
| 1/2 | blind about 0.5 dB better | blind about 2x at 2 dB |
- DVB-RCS2 is the strongest and cheapest pilot receiver (0.034-0.045 M MACs per core). At R = 1/10, -5 dB it has a floor
  from CFO window misses (its single-symbol pilots only resolve |f| < 0.025).
- The 4th-power pre/post receiver fails below 0 dB (BLER 0.5-0.9).
- At R = 2/5 blind is slightly below the genie curve: separate simulations, and blind's CRC search over several CFO
  candidates gives it extra decode attempts.
- Details and numbers: [testing/results/expected_est4.md](../testing/results/expected_est4.md).

## Earlier figures (2026-11-12, presentation receiver)

Made by [est3/plots.py](../../est3/plots.py). The pilot curves in these have the 128 pilots INSIDE the packet and their
energy is NOT charged, so for the blind-vs-pilot comparison use the `*_fair` figures above.
| Files | What it shows |
|---|---|
| `bler_best_R*.png` | BLER: blind, ML direct (128 pilots), Mengali-Morelli. Superseded by `bler_fair_R*.png` |
| `bler_more_R*.png` | BLER: the above plus joint CFO / channel ML and the CNN estimator. Superseded by `bler_fair_R*.png` |
| `macs_R*.png` | MACs of blind vs the 128-pilot receivers (the receiver of 2026-11-12; the testing receiver is 25-45 % cheaper per core at 1/10, 0.15) |
| `bler_vs_cap_R*.png` | BLER of blind vs a hard cap on the MACs of each packet (still valid) |
| `stages_R*.png` | Share of packets not yet decoded after each stage of the blind receiver (still valid) |
| `stage_pass_R*.png` | Probability that a packet reaching a stage is not decoded there (still valid) |

## Regenerate

```
py BLIND_IMPLEMENTATION/testing/plot_pres.py     # bler_fair_*, macs_fair_* (also kept in testing/results/plots/)
py est3/plots.py                                 # the earlier figures
```
