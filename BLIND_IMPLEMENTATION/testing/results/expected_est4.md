# est4: fair pilot competitors (pilots OUTSIDE the packet, energy charged) + DVB-RCS2 receivers + phase noise
Predictions written 2026-11-15 before any code or result. Sources: `lit_dvbrcs2.md` (EN 301 545-2 Table A-1, Griebel et
al. 2021, Ying-Ghogho 2005, Barbieri-Colavolpe 2007).

## Setup (what changes vs est3)
- The 1024 data symbols carry the whole codeword (N = 2048, CRC-16, interleaver), exactly as in the blind packet. Known
  symbols are EXTRA symbols in the burst (burst = 1024 + Nk symbols); the decoder sees only the 1024 data symbols.
- Every symbol has the same Es. Simulated at per-symbol Es/N0; plotted at the burst energy per data symbol,
  SNR = Es/N0 + 10 log10((1024 + Nk) / 1024) (blind: + 0). Throughput (airtime) 1024 / (1024 + Nk) reported apart.
- Same back-end for all: pre-MF correction at f_hat, LS gain / phase on the receiver's own known symbols, CA-SCL-8, the
  blind receiver's re-encoding check (RHO_N), the fair CRC search (PM+all: f_hat first, then neighbours in list-1
  metric order), window from the receiver's own CRB. Same data / CFO / phase / noise / phase noise for every receiver.
- Wiener phase noise (linewidth x Ts) on the whole burst, as blind_cfo (BLIND_PN), levels 0, 1e-5, 1e-4, 3e-4.

## Receivers
| Name | Known symbols (Nk, energy) | CFO estimate | Phase |
|---|---|---|---|
| C3 `pre128 ML` | 128-symbol preamble (0.51 dB) | ML direct (FFT 512 + 2 Newton), as est3 | one LS phase (constant) |
| C3 `pre128 M&M` | same | Mengali-Morelli (existing baseline) | constant |
| C4 `split64 ML` | 64 preamble + 64 postamble (0.51 dB) | joint ML over both blocks (FFT + Newton, lobe pick) | constant; C4b: linear interpolation of the two block phases |
| C1a `RCS2-13` | DVB-RCS2 ID 13 scaled: preamble 32, 53 x (19 data + 1 pilot), 17 data, postamble 31: Nk = 116 (0.47 dB) | Rife-Boorstyn FFT over all known symbols (zeros at data) + parabolic interpolation | constant |
| C1b `RCS2-13 track` | same | same | per-pilot phase, smoothed (sliding window), linearly interpolated across the data |
| C2 `RCS2 pre/post` | preamble 16 + postamble 16 (0.13 dB) | 4th-power FFT over the whole burst (NDA), refined on the 32 known symbols; pi/2 ambiguity from the known symbols | constant |
| genie | none (0 dB) | true CFO | true phase (incl. the phase noise path: an upper bound, no pilots) |

## Predictions (no phase noise; BLER at the PLOTTED SNR, i.e. energy charged)
- C3 ML vs est3 ML direct PM+all: same BLER at the same per-symbol Es/N0 (the decoder sees the same 1024 data symbols),
  so on the plot shifted right by 0.51 dB. In the steep waterfall that is x5-15 BLER at the same plotted SNR.
- Blind vs the best pilot receiver at R = 1/10 and 0.15: the 0.5-0.7 dB gap closes to -0.2 ... +0.2 dB; at R = 2/5 and
  1/2 blind is better by ~0.4-0.6 dB.
- C4 / C1a vs C3: same waterfall BLER within +-15 % (the CFO error is already near-genie), 2-4x fewer extra decodes
  (CRB 4-8x lower -> smaller window), floor <= C3's.
- C2: 4th-power NDA at low SNR fails often (the blind fast path is off below 0 dB for that reason): BLER x10-100 vs C3 at
  1/10 -5 ... -3 dB and 0.15 -4 ... -2 dB; within x2 of C3 from 2/5 1 dB and at 1/2.
- MACs per core: C1a / C4 <= C3 (fewer search decodes); C2 adds the 4th-power FFT (~0.1-0.2 M total).

## Predictions with phase noise (1/10 -5 dB, 0.15 -3.5 dB, 2/5 0.5 dB; 64k each, as the blind pn runs)
Phase drift std from the preamble to the last data symbol ~ sqrt(2 pi lw x 1100): 1e-5 0.26 rad, 1e-4 0.83 rad, 3e-4 1.4 rad.
- 1e-5: every receiver x1 ... x1.5.
- 1e-4: C3 (preamble only, constant phase) collapses: BLER > 0.1 at every point (worse than blind's x3-36). C4 constant
  phase x10-100; C4b (interpolated) x2-10. C1b (tracking) the best pilot receiver: x1 ... x3 at 1/10, 0.15, x2-10 at 2/5.
  C1a (constant) like C4.
- 3e-4: C1b x5-50 (the literature estimate: 16-21 deg residual at -5 dB); all constant-phase receivers BLER > 0.3.
- So under phase noise only a tracking pilot receiver (C1b) beats blind; blind needs phase tracking to compete.

## Code review (2026-11-15, code-verifier): GO with fixes
- Fixed: phase-noise runs got paired pn = 0 parts at seed 55 (e4-pn10-0, e4-pn15-0, e4-pn25-0): exact pairs per pn level.
- Reading rules: (a) RHO_N is clamped below its table at 1/10 -5.5, 2/5 0 and 1/2 1.5 dB (looser check): watch
  undetected there. (b) Different layouts have different noise draws: McNemar only within a layout; between layouts
  unpaired intervals (differences of ~5 errors in 480k are not resolvable). (c) The FFT estimators (split64 ML, RB, NDA4)
  are charged a full 8192-point FFT (~12-14 % of their per-core cost): report the estimator share apart. (d) est4's genie
  (true CFO + true phase path, no search) is NOT est3's "Genie CFO".
- Runtime estimate: e4-15 ~4 h, e4-10 ~3.5 h, e4-25 ~3 h, e4-2 ~2.5 h, pn jobs < 1 h.

## Smoke 1 (e4-smoke, 0.15 per-symbol -4 dB, 800 packets; 2026-11-15): FAIL -> fixes
EVAL DONE + ALL DONE, no Traceback. Errors pn 0 / pn 1e-4: Genie 1 / 0, RCS2-13 1 / 42, RCS2-13 track 113 / 145, pre128
ML 4 / 35, pre128 M&M 2 / 42, split64 ML 491 / 546, split64 interp 493 / 559, RCS2 pre/post 772 / 785.
- split64: rmse 9.1e-4 = the lobe spacing 1/1088: wrong lobe, out of the CRC window (M = 3). Fix: CRC search over the
  lobes m = -2..2 (the decoder picks the lobe, Barbieri-Colavolpe), metric-ordered.
- RCS2-13 track: a 9-pilot sliding window leaves ~0.37 rad at -4 dB. Fix: Kalman / RTS smoother tuned to the true
  linewidth (best-tuned competitor; reduces to the constant phase at pn 0).
- RCS2 pre/post: the 4th-power estimate fails at -4 dB (rmse 2.4e-2), as predicted.
- pn 1e-4 at -4 dB already costs the preamble receivers x9-20 (pre128 ML 4 -> 35).

## Fixes after smoke 1 (2026-11-15) and their review (GO with fixes, applied)
- split64 / prepost16: CRC search over lobes m = -3..3 (the joint ML picks a wrong lobe in 54 % of packets at -4 dB,
  58 % at -5 dB; +-3 lobes cover ~99 %); +42 metric hypotheses (still 2 rounds of 32) for failing packets.
- Phase tracking (RCS2-13 track, split64 interp): Kalman / RTS smoother, q = 2 pi pn with the TRUE linewidth (a
  favourable, best-tuned assumption for the competitor); at pn 0 it is the constant gain and is charged as const.
  rms phase error at -4 dB (rcs13): pn 1e-4 0.371 (const) -> 0.249 rad; 3e-4 0.657 -> 0.423 rad.
- Smoke 2 (e4-smoke2) with these fixes runs before the full jobs.

## Smoke 2 (e4-smoke2, 0.15 per-symbol -4 dB, 800 packets): PASS
EVAL DONE + ALL DONE, no Traceback. Errors pn 0 / pn 1e-4: Genie 1 / 0, RCS2-13 1 / 42, RCS2-13 track (Kalman) 1 / 15,
pre128 ML 4 / 35, pre128 M&M 2 / 42, split64 ML 1 / 97 (lobe error 61 %, in-search 100 % / 92.5 %), split64 interp 1 / 91,
RCS2 pre/post 715 / 721 (NDA in-search 11 %, ~68 decodes per packet).
- RCS2 pre/post runs in its own job e4-pp (same seeds, --min-err 200: stops early where it fails) and not in the pn jobs;
  the main jobs run the other 7 sources.

## Measured: phase noise (e4-pna, e4-pnb; 64k per point, seed 55, paired across pn; EVAL DONE + ALL DONE, no Traceback)
Errors (undetected) at the per-symbol Es/N0 of the point (pilot energy NOT charged here: the pilot receivers have
0.47-0.51 dB more energy per packet than blind). Blind (testing receiver, other packets, 64k, expected_cap_pn_comb.md).
| Point | pn | blind | RCS2-13 track | RCS2-13 const | pre128 ML | pre128 M&M | split64 / interp | genie (true phase path) |
|---|---|---|---|---|---|---|---|---|
| 1/10 -5 dB | 0 | 14 | 25 | 25 | 4 | 207 | 84 / 84 | 1 |
| | 1e-5 | 8 | 23 | 23 | 6 | 220 | 104 / 102 | 3 |
| | 1e-4 | 42 | 168 | 412 | 282 | 550 | 2565 / 2109 | 2 |
| | 3e-4 | 1712 | 1900 | 6486 | 7234 | 7567 | 15820 / 15860 | 2 |
| 0.15 -3.5 dB | 0 | 40 | 4 | 4 | 5 | 10 | 17 / 17 | 9 |
| | 1e-5 | 47 | 4 | 5 | 7 | 14 | 26 / 19 | 12 |
| | 1e-4 | 144 | 94 | 609 | 720 | 713 | 4035 / 4044 | 8 |
| | 3e-4 | 3962 | 1427 | 9813 | 12145 | 12211 | 21169 / 23527 | 3 |
| 2/5 0.5 dB | 0 | 147 | 155 | 155 | 226 | 231 | 144 / 144 | 216 |
| | 1e-5 | 186 | 281 | 291 | 374 | 371 | 567 / 536 | 210 |
| | 1e-4 | 5312 | 1967 | 11116 | 14286 | 14300 | 21228 / 23317 | 175 |
| | 3e-4 | 34600 | 8586 | 42951 | 47397 | 47418 | 49358 / 52527 | 190 |
Undetected <= 5 per 64k everywhere.
- RCS2-13 at 1/10 -5 dB pn 0: its 25 errors are the 0.04 % of packets whose RB estimate falls outside the window (1-symbol
  pilots every 20 symbols resolve only |f| < 0.025; the pre/postamble do not always fix it at -5 dB): a real property of
  the DVB-RCS2 layout at our CFO range.
- vs predictions: 1e-5 x1-1.5: HIT except split64 (x1.2-3.9). 1e-4: preamble receivers "collapse > 0.1 everywhere":
  only at 2/5 (0.22); x9-140 at 1/10, 0.15: PARTIAL. RCS2-13 track "x1-3 at 1/10, 0.15": MISS, x7 and x23 (the Kalman
  smoother at -5 / -3.5 dB with single-symbol pilots leaves ~0.25 rad). 3e-4 track "x5-50": MISS high at 0.15 (x360).
  Tracking always beats constant phase (x2.5-6.5): HIT. Genie with the true phase path flat in pn: as expected.
- Reading: under phase noise the DVB-RCS2 tracking receiver is the strongest pilot competitor. At the per-symbol SNR
  (pilot energy not charged) it beats untracked blind at 0.15 (x1.5 / x2.8) and 2/5 (x2.7 / x4), loses at 1/10 at 1e-4
  (168 vs 42) and ties at 3e-4. Every pilot receiver without tracking is worse than blind at 1e-4 and 3e-4. Blind's own
  tracking (pns) is the next test.

## Measured: main runs, no phase noise (e4-10, e4-15, e4-25, e4-2, e4-pp*; 480k per point, 12k-463k for pre/post; 2026-11-15)
EVAL DONE + ALL DONE, no Traceback. Plots: plots/e4_bler_R*.png, plots/e4_macs_R*.png (testing/plot_e4.py). SNR = plotted
(pilot energy charged). Blind = adopted testing receiver (1/10, 0.15; 64k per SNR) / presentation BLER + q_fix (2/5, 1/2).
SNR where BLER crosses a target (log-linear interpolation; blind points at 1/10, 0.15 have 1-45 errors: +-0.1 dB):
| Rate, target | blind | RCS2-13 | pre128 ML | split64 ML | pre/post 4th power | est4 genie |
|---|---|---|---|---|---|---|
| 1/10, 1e-4 | -4.9 | -4.09 | -4.68 | -2.87 | fails | -5.19 |
| 0.15, 1e-3 | -3.60 | -3.45 | -3.44 | -3.34 | fails | -3.91 |
| 0.15, 1e-4 | -2.98 | -3.12 | -3.12 | -2.71 | fails | -3.59 |
| 2/5, 1e-3 | 0.61 | 1.10 | 1.16 | 1.12 | fails | 0.64 |
| 1/2, 1e-3 | 1.79 | 2.33 | 2.41 | 2.38 | 2.77 | 1.90 |
MACs per core (M, scheduled) in the waterfall: RCS2-13 0.034-0.045 (the cheapest: estimator 16-21 %), split64 0.06-0.09
(est 8-15 %), pre128 0.05-0.12; blind 0.17-0.41 (1/10, 0.15), 0.23 / 0.12 (2/5 0.5 / 1 dB), 0.083 (1/2 2 dB).
- vs predictions: "gap at 1/10, 0.15 closes to -0.2 ... +0.2 dB": HIT (0.15: blind +0.15 dB better at 1e-3, -0.14 dB at 1e-4;
  1/10: blind +0.2 dB better than pre128 ML at 1e-4). "2/5, 1/2 blind better by 0.4-0.6 dB": HIT (0.49-0.54 dB).
  "C4 / C1a vs C3 same waterfall": HIT at 0.15, 2/5, 1/2; at 1/10 split64 is worse (lobe errors at -5 dB) and RCS2-13 has
  the window-miss floor (881 / 480k at -5 dB). "C2 x10-100 at low SNR": HIT (BLER 0.5-0.9 below 0 dB).
- pre128 has an undetected floor of 2-6 per 480k at every SNR (wrong CRC passes); RCS2-13 and split64 have none.
- Net: with the pilot energy charged blind matches or beats every pilot receiver in BLER at all 4 rates, at 2-10x the
  MACs per core (vs RCS2-13: x5-12 at 1/10, 0.15, x6 at 2/5 0.5 dB, x2 at 1/2 2 dB).
