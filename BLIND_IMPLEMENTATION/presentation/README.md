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

What they show (numbers updated 2026-11-17 for the adopted testing receiver and the fixed DVB-RCS2 search, which the
figures now show solid next to the old search dashed; the figures' receiver set is the est4
one above; every deployed competitor is in [../testing/results/scoreboard.md](../testing/results/scoreboard.md)):
| Rate | BLER (required SNR, blind vs best pilot receiver in these figures) | MACs per core at blind's crossing |
|---|---|---|
| 1/10 @1e-4 | blind -4.78 vs 128 ML -4.72: tie (+0.06); DVB-RCS2 with the fixed search -4.58 (+0.20; old search -4.09, +0.69) | blind 0.194 M = 5.7x DVB-RCS2, 2.2x 128 ML |
| 0.15 @1e-3 | blind -3.60 vs DVB-RCS2 -3.45: blind 0.15 dB better | blind 0.262 M = 7.5x DVB-RCS2 |
| 0.15 @1e-4 | blind -2.93 vs DVB-RCS2 / 128 ML -3.12: blind 0.19 dB worse | blind 0.180 M = 5.1x DVB-RCS2 |
| 2/5 @1e-3 | blind 0.58 vs DVB-RCS2 1.10: blind 0.52 dB better | blind 0.183 M = 4.6x DVB-RCS2 |
| 1/2 @1e-3 | blind 1.73 vs DVB-RCS2 2.33: blind 0.61 dB better | blind 0.139 M = 3.2x DVB-RCS2 |
- DVB-RCS2 is the strongest and cheapest pilot receiver (0.034-0.045 M MACs per core). At R = 1/10, -5 dB it has a floor
  from CFO window misses (its single-symbol pilots only resolve |f| < 0.025).
- The 4th-power pre/post receiver fails below 0 dB (BLER 0.5-0.9).
- At R = 2/5 blind is slightly below the genie curve: separate simulations, and blind's CRC search over several CFO
  candidates gives it extra decode attempts.
- Details and numbers: [testing/results/expected_est4.md](../testing/results/expected_est4.md).

## Every compared receiver, full curves (2026-11-17)
BLER vs SNR and MACs per core vs SNR of blind and all 31 compared receivers, one panel per system family:
`../testing/results/plots/curves_bler_R*.png`, `curves_macs_R*.png`; every point in
[../testing/results/curves.md](../testing/results/curves.md) (made by `testing/plot_curves.py`).

## Earlier figures (2026-11-12, presentation receiver)

Made by [est3/plots.py](../../est3/plots.py). The pilot curves in these have the 128 pilots INSIDE the packet and their
energy is NOT charged, so for the blind-vs-pilot comparison use the `*_fair` figures above. The superseded
`bler_best`, `bler_more` and `macs` figures were deleted on 2026-11-17 (recoverable from git commit 0e0eee8).
| Files | What it shows |
|---|---|
| `bler_vs_cap_R*.png` | BLER of blind vs a hard cap on the MACs of each packet (still valid) |
| `stages_R*.png` | Share of packets not yet decoded after each stage of the blind receiver (still valid) |
| `stage_pass_R*.png` | Probability that a packet reaching a stage is not decoded there (still valid) |

## Regenerate

```
py BLIND_IMPLEMENTATION/testing/plot_pres.py     # bler_fair_*, macs_fair_* (also kept in testing/results/plots/)
py est3/plots.py                                 # the earlier figures
```
