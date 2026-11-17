# fx: three key competitors on the FIXED search (predictions 2026-11-17, before the run)

**Why (user, 2026-11-17):** the three code reviews found that two of the three key competitors lose packets to holes
in their CFO search, not to their estimators. Test: pre128 ML (strongest mathematical reference; no search defect
found, run as the control), DVB-RCS2 ID 13 with the search widened over its pre/post side peaks ("RCS2-13 wide"),
VDE-SAT with an unclipped alias window, +-2 aliases and wider alias windows ("VDE-SAT fixed"). 480k packets per point,
6 parallel jobs (fx-10a: data Es/N0 -5.4 -5.2, fx-10b: -4.8 -4.4, fx-15a: -4 -3.5, fx-15b: -3 -2.5, fx-25: 0 0.5 1,
fx-2: 1.5 2 2.5; seeds 182-187), ~40 min budget. RCS2-13 wide: window +-1e-2 (M = 134): the code-editor's noise-free
check showed the pre/post side peaks continue across the whole range at ~60/116 height (23 peaks > 30 in [0, 0.06]),
so +-3e-3 would have caught only the first 3 each side. VDE-SAT at -5.4 plots at -5.13 and is not used. Blind (adopted testing receiver):
1/10 -4.78 @1e-4; 0.15 -3.60 @1e-3, -2.93 @1e-4; 2/5 0.58; 1/2 1.73 @1e-3.

## Predicted required SNR (fair axis) and gap to blind (+ = blind better)
| Receiver | 1/10 @1e-4 | 0.15 @1e-3 | 0.15 @1e-4 | 2/5 @1e-3 | 1/2 @1e-3 | MACs per core |
|---|---|---|---|---|---|---|
| pre128 ML (control; old -4.68 / -3.44 / -3.12 / 1.16 / 2.41) | -4.73 ... -4.63 (+0.05 ... +0.15) | -3.47 ... -3.41 (+0.13 ... +0.19) | -3.17 ... -3.07 (-0.24 ... -0.14) | 1.14 ... 1.18 (+0.56 ... +0.60) | 2.39 ... 2.43 (+0.66 ... +0.70) | ~0.07-0.09 M (unchanged) |
| RCS2-13 wide (old -4.09 / -3.45 / -3.12 / 1.10 / 2.33) | **-4.80 ... -4.65 (-0.02 ... +0.13)** | -3.50 ... -3.44 (+0.10 ... +0.16) | -3.20 ... -3.10 (-0.27 ... -0.17) | 1.08 ... 1.12 (+0.50 ... +0.54) | 2.31 ... 2.35 (+0.58 ... +0.62) | 0.034-0.04 M (extra metric passes only on failing packets) |
| VDE-SAT fixed (old fails / -2.92 / -1.77 / 0.92 / 2.16) | **-4.85 ... -4.60 (-0.07 ... +0.18)** | **-3.62 ... -3.48 (-0.02 ... +0.12)** | **-3.25 ... -3.00 (-0.32 ... -0.07)** | 0.88 ... 0.94 (+0.30 ... +0.36) | 2.12 ... 2.18 (+0.39 ... +0.45) | 0.035-0.05 M |
Method: genie + pilot energy (+0.466 RCS2, +0.271 VDE, +0.512 pre128) + residual estimation loss; the search holes
removed means the old in-search misses (RCS2 1/10: ~130 of 158 errors at -5 dB; VDE: misses ~= errors) go away.

**Verdict to expect:** blind's lead at 1/10 over DVB-RCS2 (+0.69) and VDE-SAT ("fails") shrinks to about a tie;
at 0.15 @1e-4 VDE-SAT joins the receivers that beat blind. At 2/5 and 1/2 nothing changes (their searches were not
missing packets there). Blind keeps a 3-6x MACs disadvantage against these three.

Kill / flag rules: the control (pre128 ML) must reproduce its old crossings within +-0.05 dB, else the run is
suspect; the fixed sources must have in-search >= 0.9999 at every point, else the fix is incomplete.

## Measured (2026-11-17 10:20; fx-10a/b, fx-15a/b, fx-25p1/p2/r, fx-2p/r all ALL DONE, no Traceback)
Crossings from the scoreboard generator (plot_e4.gap_db over the pooled parts; pre128 ML pools the new fx rows with its
e4 rows). fx-25 / fx-2 (first version with the 0 / 1.5 dB points, ETA 4-5 h) were deleted with the user's approval and
re-split without the lowest point.
| Receiver | 1/10 @1e-4 | 0.15 @1e-3 | 0.15 @1e-4 | 2/5 @1e-3 | 1/2 @1e-3 | MACs per core |
|---|---|---|---|---|---|---|
| Blind | -4.78 | -3.60 | -2.93 | 0.58 | 1.73 | 0.194 / 0.262 / 0.180 / 0.183 / 0.139 |
| pre128 ML (control) | **-4.72 (+0.06)**, was -4.68 | -3.44 (+0.16) | -3.10 (-0.17), was -3.12 | 1.16 (+0.59) | 2.41 (+0.69) | 0.09 / 0.078 / 0.075 / 0.085 / 0.068 |
| RCS2-13 wide | **-4.58 (+0.20)**, was -4.09 (+0.69) | -3.44 (+0.16) | -3.09 (-0.16) | 1.09 (+0.51) | not bracketed (3.4e-4 at 2.47; old 2.33) | 0.034 / 0.040 / 0.036 / 0.046 / - |
| VDE-SAT fixed | fails (6.0e-3 at -4.13, in-search 0.982-0.994) | -3.06 (+0.54), was -2.92 | fails in the run range (1.8e-4 at -2.23) | 0.91 (+0.33) | not bracketed (4.6e-4 at 2.27; old 2.16) | 0.035-0.041 |
- **Control passes:** pre128 ML reproduces its old crossings within 0.04 dB (0.15) and moves -0.04 dB at 1/10 with the
  new packets (pooled 1/10 gap +0.06: a tie with blind).
- **RCS2-13 wide: fix works, prediction missed.** in-search 0.9999-1.0000 everywhere (was 0.9997 at 1/10 -5 dB);
  1/10 gains 0.49 dB, predicted -4.80 ... -4.65, measured -4.58: some loss beyond the side peaks remains. 0.15, 2/5:
  unchanged (+-0.03), as predicted. MACs unchanged at the crossings (the extra metric passes only run on failing
  packets).
- **VDE-SAT fixed: fix insufficient.** in-search stays 0.98-0.994 at 1/10 and 0.997-0.9998 at 0.15; it still fails
  1e-4 at 1/10. Prediction (-4.85 ... -4.60) missed badly. The full-range scan (fx-s10 running, fx-s15 queued) is the
  real test; until then VDE-SAT's 1/10 result stays "fails".
- At 1/2 the fixed sources were run only at 2.0 / 2.5 dB (lowest point dropped for time), so their 1e-3 crossing is not
  bracketed; their searches were not missing packets there (in-search 1.0000), so the old crossings stand.
