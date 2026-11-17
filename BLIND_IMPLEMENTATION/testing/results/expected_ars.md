# Griebel & Wasenmüller 2021 (ARS 19, 59) variants on the DVB-RCS2 ID 13 layout: predictions 2026-11-15, before code
Source: lit_ars2021.md (full text read). The paper = our est4 "RCS2-13" estimator (DA-KS: zero-filled r c* on all known
symbols, N-point FFT, peak + 3-bin parabolic interpolation on |X|, phase = arg X). Its claim: interpolation lets the FFT
shrink (8192 -> 2048 for 536 symbols) at ~0.1-0.2 dB. Same rcs13 layout (Nk = 116, +0.47 dB) and packets as RCS2-13, so
every variant is McNemar-paired with RCS2-13.
| Variant | What | Predicted SNR change vs RCS2-13 (plotted) | MACs per core |
|---|---|---|---|
| G4096 | FFT 4096 + parabolic | 0 ... +0.05 dB | -9 ... -11 % |
| G2048 | FFT 2048 + parabolic | +0.03 ... +0.2 dB (worst at 1/2) | -12 ... -17 % |
| G2048N | FFT 2048 + parabolic + 1 Newton step | 0 ... +0.05 dB | ~ G2048 |
| Griebel faithful | FFT 2048, peak over the full band, Eq. 17 phase (sign-corrected), ONE decode, no CRC / lobe search (the paper's chain) | +0.1 ... +0.5 dB, BLER floor at 1/10 -5 dB from the 1/20 aliases | lowest |
| RCS2-13 lobes | RCS2-13 + the +-1/20 alias lobes in the CRC search (our addition, not from the paper) | 1/10 @1e-4: -4.09 -> -4.7 ... -4.55 dB (gap to blind 0.2-0.35 dB); others unchanged | +small at -5 dB |
- Blind's lead at 0.15, 2/5, 1/2 is unchanged by any of these.

## Predicted comparison with blind (written before the runs, 2026-11-15)
Required SNR [dB] on the fair axis (pilot energy charged). **Gap = variant - blind: positive = blind better.** RCS2-13 and
blind are measured (8.2a); the variants are predictions (RCS2-13 + the change in the table above). All variants use the
same 116 known symbols (+0.47 dB).

| Variant | 1/10 @1e-4 (blind -4.90) | 0.15 @1e-3 (blind -3.60) | 0.15 @1e-4 (blind -2.98) | 2/5 @1e-3 (blind 0.61) | 1/2 @1e-3 (blind 1.79) | MACs per core (blind / variant) |
|---|---|---|---|---|---|---|
| RCS2-13 (measured) | -4.09 (gap +0.81) | -3.45 (+0.15) | -3.12 (-0.14, RCS2-13 better, inside blind's CI) | 1.10 (+0.49) | 2.33 (+0.54) | 0.034-0.043 M: blind 2-6x more |
| G4096 | +0.81 ... +0.86 | +0.15 ... +0.2 | -0.14 ... -0.09 | +0.49 ... +0.54 | +0.54 ... +0.59 | ~10 % below RCS2-13 |
| G2048 | +0.84 ... +1.0 | +0.18 ... +0.35 | -0.11 ... +0.06 | +0.52 ... +0.69 | +0.57 ... +0.74 | 12-17 % below RCS2-13 |
| G2048N | +0.81 ... +0.86 | +0.15 ... +0.2 | -0.14 ... -0.09 | +0.49 ... +0.54 | +0.54 ... +0.59 | ~ G2048 |
| Griebel faithful (one decode) | +0.9 ... +1.3, BLER floor | +0.25 ... +0.65 | -0.04 ... +0.36 | +0.6 ... +1.0 | +0.65 ... +1.05 | lowest (one decode) |
| RCS2-13 lobes | -4.7 ... -4.55 (+0.2 ... +0.35) | +0.15 | -0.14 | +0.49 | +0.54 | + a few decodes at -5 dB |

Summary prediction: the paper's FFT shortcuts only make DVB-RCS2 slightly worse and cheaper, so blind's lead grows by
0-0.5 dB. The one variant that helps DVB-RCS2 is ours (RCS2-13 lobes): it cuts blind's lead at 1/10 from 0.81 to
0.2-0.35 dB and becomes the fairest DVB-RCS2 competitor. Blind still wins at 1/10, 0.15 @1e-3, 2/5 and 1/2; 0.15 @1e-4
stays a tie (RCS2-13 0.14 dB ahead, inside blind's CI [-3.17, -2.57]).
- Kill / keep: a variant replaces RCS2-13 as the reference only if paired BLER is not worse (p >= 0.05) — RCS2-13 lobes is
  then the strongest DVB-RCS2 competitor and the fair one to show.

## Measured (2026-11-15; ars-10/15/25/2, 480k packets per point, paired with RCS2-13; verified ALL DONE, no Traceback)
Regression check passed: RCS2-13 here = e4-10/15/25/2 bit-exactly at all 27 points (errors, packets, rmse).

Required SNR [dB] on the fair axis; (gap to blind, + = blind better):
| Variant | 1/10 @1e-4 | 0.15 @1e-3 | 0.15 @1e-4 | 2/5 @1e-3 | 1/2 @1e-3 | MACs per core [M] |
|---|---|---|---|---|---|---|
| Blind (testing model, 8.2a) | -4.90 | -3.60 | -2.98 | 0.61 | 1.79 | 0.08-0.26 |
| RCS2-13 | -4.09 (+0.81) | -3.45 (+0.15) | -3.12 (-0.14) | 1.10 (+0.49) | 2.33 (+0.54) | 0.034-0.045 |
| G4096 | -3.97 (+0.93) | -3.45 (+0.16) | -3.11 (-0.13) | 1.10 (+0.49) | 2.33 (+0.54) | 0.030-0.042 (-10 %) |
| G2048 | -1.15 (+3.75) | -2.88 (+0.72) | -1.34 (+1.64) | 1.10 (+0.49) | 2.33 (+0.55) | 0.028-0.041 (-15 %) |
| G2048N | -1.15 (+3.75) | -2.88 (+0.72) | -1.34 (+1.64) | 1.10 (+0.49) | 2.33 (+0.54) | ~ G2048 |
| Griebel faithful | -1.08 (+3.82) | -2.72 (+0.88) | -1.26 (+1.72) | 1.29 (+0.68) | 2.55 (+0.76) | 0.028-0.036 |
| RCS2-13 lobes | -4.10 (+0.80) | -3.45 (+0.15) | -3.12 (-0.14) | 1.10 (+0.49) | 2.33 (+0.54) | 0.034-0.047 |

Scoring the predictions:
- G4096: predicted 0 ... +0.05 dB vs RCS2-13 -> measured 0 at 0.15, 2/5, 1/2, +0.12 at 1/10. Hit (slightly worse at 1/10).
- G2048: predicted +0.03 ... +0.2 -> measured 0 at 2/5, 1/2 but +2.7 (1/10), +0.57 / +1.78 (0.15). **Miss at low SNR.**
  Cause: the 2048-point FFT zero-pads our ~1140-symbol rcs13 burst only 1.8x (the paper: 2048 for 536 symbols, 3.8x);
  at -5 ... -2 dB the 3-bin parabola then picks a neighbouring bin (rmse 6.7e-4 vs 2.2e-4 at 1/10 -5 dB; in-window
  0.9934 = the error count). One Newton step (G2048N) cannot recover a wrong bin: identical errors. At 2/5, 1/2 (SNR >= 0)
  the peak is never missed; only the parabolic bias remains (rmse 4.5e-5 vs 2e-5), harmless for BLER.
  So G2048 is NOT the paper's operating point; the paper-equivalent size for our burst is G4096.
- Griebel faithful: predicted +0.1 ... +0.5 -> +0.19 / +0.22 at 2/5, 1/2 (hit); much worse at low SNR (same FFT-size cause
  plus no CRC / lobe search).
- RCS2-13 lobes: predicted 1/10 -4.7 ... -4.55 -> measured -4.10 (no gain). **Miss:** RCS2-13's 1/10 errors are not 1/20
  alias lobes (lobe_err 0, in-window 0.9997 at -5 dB); its loss to blind there is CFO accuracy at -5 dB, not aliasing.
- Blind's lead: predicted unchanged by every variant -> confirmed; the best DVB-RCS2 variant is still RCS2-13 / G4096.

Fairness note: "Griebel faithful" also uses FFT 2048, so at 1/10, 0.15 it carries the same too-coarse grid. A faithful
chain at 4096 would sit near G4096 minus the CRC search; not run (it cannot beat RCS2-13, which already has the search).

