# Tuning record: blind receiver on the full-system formats (DVB-RCS2 ID 3/13/14/42, VDE-SAT Link 32)

Started 2026-11-17. This file is the evidence for every threshold the full-system blind receiver uses: what data each
choice was made on, what was rejected and why, and how it was checked. All raw data is kept (see "Data").

## Rules
- Thresholds are chosen on **calibration packets** only (`run_blind_fs --calib`: seed tag + 500000, disjoint from every
  test run), early stops off, every decode logged (`--dump`).
- Selection rule: the cheapest setting (mean MACs per core) whose extra errors are <= floor(0.02 x no-stop errors) at
  **every** calibration point.
- The choice is then replayed on the **test packets** (paired, same packets with and without the setting) and, if
  adopted, checked **live on fresh seeds**. Final curves use a further fresh seed range (70xx).
- Checkpoint-NN training uses its own seed range (tag + 900000), disjoint from tests and calibration.

## F5 early stop (frozen-bit path-metric stop): `plots/DVB-RCS2/tuning/fs_tuning_f5.png`
Replayed with `fullsys/tune_blind_fs.py`; sweep data in `fullsys/results/tuning_f5_sweep.json`.

| Format | Calibration parts | Picked on calibration | Test replay | Live check (fresh seeds) | Adopted |
|---|---|---|---|---|---|
| ID 13 | fs-k13m08/m06/m04/m02 (4 x 4-8k pkts) | q 0.6, t 0.78 (mean -8 %) | lost 2 at -0.6 dB, 2 at 0.0 dB | t 0.80: fs-l13 -0.6 dB 20/20000, -0.4 dB 5/20000, ~5 % fewer MACs | **q 0.6, t 0.80** |
| ID 3 | fs-k3 (-0.8, -0.4), fs-k3b (-0.2, 0.0, +0.2) | 1st try q 0.9 t 0.78: lost 12/30 at -0.2 and 0.0 dB on test; 2nd try q 0.8 t 0.86 | 2nd try: lost 1 each at +0.2/+0.4/+0.6 dB, saving 1-7 % | - | **none** |
| ID 42 | fs-k42 (-4.0, -3.8) | q 0.9, t 0.75 | lost 3 of ~345k pkts (2 at -4.2, 1 at -4.0), saving 5-11 % | fs-l42: same BLER, 0.84 vs 0.98-1.16 M at -4.0 dB | **q 0.9, t 0.75** |
| ID 14 | fs-k14 (1.4, 1.6) | q 0.7, t 0.78 | lost 0 of 65k, saving up to 25 % at 1.4 dB | fs-l14: same BLER, 0.42 vs 0.52 M at 1.4 dB | **q 0.7, t 0.78** |
| VDE 32 | fs-kv32 (-5.6, -5.0, -4.4) | q 1.0, t 0.75 | lost 1 at 4 of 7 points, saving ~3 % | - | **none** |

Caveat (ID 13): t 0.80 was chosen after the calibration pick (0.78) lost packets in the test replay, by replaying the
next safer thresholds on all logged packets (test included). The live check and the final curve use fresh packets, so
the reported curves are not biased by it.

## MAC cap / stage cut-off
Offered to the tuner together with F5 (caps none/1/1.5/2/3/5/8 M, stage cut 2-5): no cap or stage cut ever passed the
2 % rule at the operating points. Cap trade-off curves: `plots/DVB-RCS2/MACs/fs_blind_capcurve.png`, `plots/DVB-RCS2/MACs/fs_bler_vs_budget.png`,
`plots/DVB-RCS2/BLER/fs_bler_capped.png` (data `fullsys/results/capcurve_id13_3_42.json`). No cap adopted (user decision pending for
worst-case plots).

## Checkpoint NN
Per-format retraining (`fullsys/ck_nn_fs.py`, jobs fs-cktr3/13/14/42, fs-cktrv32), paired tests vs old NN and NN off on the
same packets (fs-t3nn, fs-t13nn, fs-t42nn, fs-t14nn, fs-nn*): `plots/DVB-RCS2/tuning/fs_nn_compare.png`. Retrained NN adopted for all
four DVB-RCS2 IDs (same BLER, 11-64 % fewer MACs at the low-SNR end). VDE: own NN (fs-cktrv32, c 3) in the final runs
fs-gv32* (BLER -4.6 dB 3e-4 vs 7.7e-4 without, paired fs-tv32nn vs fs-bv32).

## Z-test (live grid on calibration packets, `fullsys/zt_compare.py`, output `fullsys/results/zt_compare_2026-11-17.txt`)
Settings k1 NN shortlist ck_keep 0.01 / ck_min 4 (+ tau 0, kmin 4 on DVB), k2 phase_keep (VDE: tau 0, kmin 4), k3 win 4.5,
k4 final 16, k5 first_k null (DVB) / batch null (VDE). Result 2026-11-17:
- DVB: nothing worth adopting. k1 fails everywhere (ID 3 +173 / +107 errors) but cuts the WORST case 65-82 %; k2-k5 within
  the 2 % rule at most points but save only 0-5 % mean (ID 42 k4 final 16: -5 / -9 %, 0 extra errors).
- VDE: k5 batch null: identical decisions (0 new / 0 fixed errors) and -63 % (-5.0 dB) / -40 % (-5.4 dB) mean MACs per
  core, max -8 %; k4 final 16: identical decisions, -3 / -15 % mean, max -34 %. k1 (shortlist only, no tau change) 0 extra
  errors; k2 (tau 0, kmin 4) +17 / +21 errors -> the DVB k1 losses are probably the tau / kmin part.
- Follow-up (submitted): DVB k6 = shortlist only (ck_keep 0.01, ck_min 4), k7 = milder (ck_keep 0.003, ck_min 8);
  VDE batch null (+ final 16) at -6.6 ... -4.6 dB (fs-cv32h..m).
- VDE batch null + final 16 (fs-cv32h-m, plot `plots/VDE-SAT/tuning/fs_vde_mac_cuts.png`): the SAME failing packets as
  the control at -6.6 / -6.2 / -5.8 / -5.4 / -5.0 / -4.6 dB (684 / 364 / 252 / 257 / 98 / 15 errors, 0 new, 0 fixed);
  mean MACs per core 6.08 -> 3.60, 3.58 -> 2.08, 1.61 -> 0.87, 0.74 -> 0.33, 0.45 -> 0.16, 0.42 -> 0.13 M (-41 ... -69 %);
  worst case 8.5 -> 4.9 M. Passes the 2 % rule -> live check on the fresh final seeds (fs-gv32na-d, paired with fs-gv32*).
  **CAVEAT (found 2026-11-17 21:40): `batch: null` without `cores` costs the search on Kc = len(g) ~ 249 cores (one per
  grid cell, small_rx Kc), not the study's 32 cores, so these MACs-per-core savings are NOT comparable. Decisions are
  unaffected. Re-costed on 32 cores: fs-jv32c0 (`{"batch": null, "cores": 32, "final": 16}`) and fs-jv32c1 (final 16
  alone on batch (32, 5.0)); numbers above to be replaced.**
- Two-pass on calibration (`twopass_cal_v32_nnfail.json`): errors identical to the NN at -5.4 / -5.0 / -4.6 dB (257 / 98 /
  17), mean 1.59 / 0.47 / 0.248 M vs NN 0.74 / 0.45 / 0.424 M; with the grid-step-8 NN as 2nd pass 267 / 106 / 20 errors.
- CFO grid step 6 / 8 and stride 3 without the NN: rejected (2-4x the errors AND more MACs). With the NN: step 8 -30 to
  -40 % mean MACs for +15-60 % errors (fails the 2 % rule; user decision).

## VDE-SAT MAC cuts (started 2026-11-17, CFO range stays +-0.03 by user decision)
Where the MACs go (fs-gv32m46, -4.6 dB, per core h+d4a): 0.423 M with the NN = CFO grid ~0.23 M (248 cells x 2 phases,
fixed per packet) + NN checkpoint cells (charge-all) + decodes; no NN 0.242 M (grid ~0.2 M). The "stage 1" 15k is the
squared-signal FFT coarse estimate (fast path already off: s0_snr 0.5), not waste. MAC caps: no use (fs_vde_capped.png, receiver before tuning, removed 2026-11-18; tuned receiver: VDE-SAT/MACs/fs_vde_tuned_capped.png:
cap 1 M -> BLER 3e-4 -> 2.9e-3 at -4.6 dB; the ~0.4 M floor is paid by every packet).

Candidates, all on calibration packets (seed 8032 --calib, -5.4 / -5.0 / -4.6 dB, paired with fs-ztv32k0):
- two-pass "NN only for rejected packets" (`fullsys/two_pass_replay.py`, exact offline from paired dumps). First look on
  the paired TEST runs bv32 / tv32nn (seed 32): -4.6 dB errors 30 / 8 / 8 (no NN / NN / two-pass), mean 0.242 / 0.423 /
  0.245 M; -5.0 dB 30 / 15 / 15, 0.461 / 0.461 / 0.497 M; -5.4 dB 33 / 26 / 26, 1.19 / 0.70 / 1.42 M; worst case 22.8 M
  (vs 8.2 M). Data `fullsys/results/twopass_test_bv32_tv32nn.json`. To be confirmed on calibration (fs-cv32a + fs-ztv32k0 / fs-cv32g).
- CFO grid step 6 / 8 (default 4): fs-cv32b / c (no NN), fs-cv32e / f (NN); coarse start stride 3: fs-cv32d.
- z-test grid fs-ztv32k0..k5.

## VDE-SAT JOINT TUNING (2026-11-17 evening; objective mean MACs, 2 % rule at every calibration point)
Base (fair 32-core cost): NN c 3 + `{"batch": null, "cores": 32, "final": 16}` (fs-jv32c0; identical decisions to the
previous final receiver, -26 ... -36 % mean MACs, worst case 8.4 -> 5.2 M).
- **Offline joint tuner** (`fullsys/joint_tune_fs.py`, full-search log mode `run_blind_fs --fulllog`): logs fs-flv32a/b/c
  (seed 8032 calib, -6.2 ... -4.6 dB, 50k packets), held-out logs fs-flv32ta/tb/tc (seed 8033). Self-check: replaying
  the logged settings reproduces all 50k packets exactly (decisions and every cost counter, 0 mismatches).
- Run 1 (fs-jtv32b, objective = mean of per-point mean MACs): pick final 0 / win 4.0 / ck_keep 0.003 / ck_min 4;
  live check fs-jv32t* confirmed the replay (fewer errors) but it costs +9 % / +18 % at -5.0 / -4.6 dB (cheap only at
  low SNR): REJECTED; the objective was changed to the mean over points of cost / baseline cost (`--objective rel`).
- Run 2 (fs-jtv32c, relative objective, 242 settings): **pick final 4, win 4.0, ck_keep 0.003, ck_min 4** (+ base).
  Replay vs the live round-2 winner r3 (final 8, win 4.5, ck_keep 0.01, ck_min 4), fs-jtv32v: identical errors on
  calibration (736 / 516 / 255 / 62 / 8 vs base 750 / 525 / 257 / 63 / 8) and on held-out (752 / 502 / 187 / 58 / 1 vs
  base 772 / 512 / 191 / 62 / 1); mean MACs pick 1.41 / 0.73 / 0.42 / 0.33 / 0.31 M vs r3 1.71 / 0.84 / 0.45 / 0.33 /
  0.32 M vs base 2.36 / 1.09 / 0.52 / 0.34 / 0.31 M; worst case 3.0 (pick) / 3.7 (r3) / 5.2 M (base).
- Live rounds (calibration, paired with fs-jv32c0): round 1 single knobs (final 8, win 4.5 pass; fine_last 2/0, T_fine 3,
  no CA retry, grid step 6 fail); round 2 r1-r3 (r3 best); round 3 r4 (final 4 + ck_min 2) FAILS (+9 / +5 at -5.0 /
  -4.6 dB), r5 (kmin 8) and r6 (ncand 2) = r3. NN checkpoint position (c 1 / c 2) no gain.
- Fresh test packets (seed 7032, paired with the previous final fs-gv32*): r3 (fs-gv32q) same errors at every point
  (-1 at -6.2 / -5.8 dB), mean MACs -54 / -52 / -49 / -39 / -28 / -26 / -28 / -36 % at -6.6 ... -3.8 dB, worst 8.4 ->
  3.7 M. Tuned pick: fs-gv32k (running) + live calibration check fs-jv32u.
- **ADOPTED (2026-11-18 00:30): the run-2 pick** `{"batch": null, "cores": 32, "final": 4, "win": 4.0, "ck_keep": 0.003,
  "ck_min": 4}`, F5 off. Live calibration check fs-jv32u: errors 729 / 508 / 248 / 61 / 6 (base 750 / 525 / 257 / 63 /
  6), 0 packets lost, mean MACs 1.41 / 0.72 / 0.42 / 0.33 / 0.31 M = the replay to 0.002 M. Fresh test packets fs-gv32k
  vs the previous final fs-gv32: same errors (31 vs 32, 30 vs 31 at -6.2 / -5.8 dB), mean MACs 2.20 / 1.44 / 0.74 / 0.41
  / 0.33 / 0.31 / 0.31 / 0.31 M at -6.6 ... -3.8 dB (-63 ... -26 %), worst case 8.4 -> 3.0 M.
- **F5 for VDE: tuned, NOT adopted.** Joint search with fzstop in the grid (fs-jtv32f, joint_v32jf5.json) picked
  F5 (1.0, 0.75) + final 2 + win 3.5: objective 0.731 vs 0.748 (~2 %), reached by pushing final / win beyond anything
  checked live; the F5 replay is pessimistic (live cross-check fs-jv32f with (0.9, 0.75) on top of the pick: errors
  735 / 514 / 259 / 61 / 7 vs replay 744 / 532 / 279 / 71 / 8; MACs -5 / -4 / -1.5 / 0 / 0 % vs the pick for +6 / +6 /
  +11 / 0 / +1 errors). User decision 2026-11-18: leave F5 out for VDE.
- MAC cap on the tuned receiver (fresh packets, capcurve_vde32_tuned.json): -4.6 dB errors 19 / 20 / 30 / 55 per
  60000 with no cap / 2 / 1 / 0.5 M; not adopted (no cap needed: worst case 3.0 M).

- **One phase guess ADOPTED (2026-11-18 01:05)** on top of the tuned pick (`nph {"0.15": [2, 0.5]}`: one phase
  hypothesis per CFO cell). Calibration: -6.2 / -5.4 / -4.6 dB 717 / 246 / 7 vs 729 / 248 / 6 (20k at -4.6), 60k:
  -5.0 91 vs base 98, -4.6 16 vs 15 (1 over the strict allowance 0). Fresh paired seeds 7032 / 7033 / 7034
  (`vde_onephase_decision.py`): pooled -5.0 dB 215 vs 214 (allowed +4), -4.6 dB 58 vs 59; -31 ... -33 % MACs at every
  SNR. Floor-cut alternatives on calibration (fs-jv32w2-w5): NN checkpoint c 1 / c 2 no gain; grid step 6 +33 / +28
  errors; c 1 + one phase = one phase alone.
- Retune on one-phase logs (fs-jtv32n, joint_v32jn.json): pick final 0, ck_min 8, tau 0, final_post 32, ncand 1;
  objective 0.637 vs 0.831 base; NOT adopted (no live check yet; final 0 was cheap only at low SNR in run 1).

## DVB-RCS2 JOINT TUNING (2026-11-18; live combinations, the offline replay does not model the joint list decodes)
Calibration packets (seeds 8003 / 8013 / 8014 / 8042 --calib), paired with the z-test control k0 (`zt_compare.py`):
- k6 shortlist only (ck_keep 0.01, ck_min 4): passes ID 13 / ID 14, fails ID 3 (+24 at -0.2 dB) and ID 42 (+11 at -3.8).
- k7 milder shortlist (0.003, 8): passes ID 13 / 42 / 14, fails ID 3 (+8, allowed 6).
- k8 = final 16 + win 4.5 + the passing shortlist: all pass. Mean MACs ID 14 -18 / -5 %, ID 42 -5 / -9 %, ID 13
  -0.4 / -2 %, ID 3 +1 / +2 % with 16 / 10 fewer errors; worst case -8 ... -31 % (ID 3 +8 %).
- k9 = final 8 + win 4.0 (ID 3: final 8 + win 4.5) + shortlist: all pass; vs k8 ID 42 -7 / -12 %, ID 14 -19 / -6 %,
  ID 3 25 / 13 fewer errors for +1 / +4 %; ID 13 no gain (+1 error, at the allowance) -> ID 13 keeps k8.
- **Adopted for the final reruns (fs-u*, seeds 7003 / 7013 / 7014 / 7042, --charge-all, part suffix jt):** ID 13 k8,
  ID 42 k9, ID 3 k9, ID 14 k9.
- Fresh-packet result (fs-u*, paired with the final runs before tuning; tables `fullsys/results/dvb_tuned_tables.md`):
  BLER unchanged (0-2 errors per point; BLER 1e-3 crossings 1.33 / 1.28 / 2.30 / 1.76 dB vs 1.34 / 1.29 / 2.33 / 1.77
  before, ID 13 / 42 / 3 / 14). Mean MACs: ID 14 -46 ... -23 % in the waterfall (+1.0 ... +1.4 dB), ID 42 -14 ... -7 %
  (-4.2 ... -3.8 dB), ~0 % from BLER ~1e-3 on; ID 13 ~0 %; ID 3 +1 ... +9 % (with a few errors fewer). Adopted as the
  final DVB-RCS2 receivers.

## Data (kept, do not delete)
- Calibration dumps: `fullsys/results/blind_fs_fs-k*_dump/`, JSON `blind_fs_fs-k*.json`.
- Test dumps: `blind_fs_fs-c*/d*/e*/bv32*_dump/`.
- Tuner outputs: `fullsys/results/tune_k13.json`, `tune_k3.json`, `tune_k3v2.json`, `tune_k42.json`, `tune_k14.json`,
  `tune_kv32.json` (calibration points, full Pareto front, best per kind, feasible top 50, test validation), replays
  `tune_rp_*.json`, `tune_x42_*.json`; sweep `tuning_f5_sweep.json`.
- NN training: `fullsys/results/ck_nn_fs_fs-cktr*.json` (history, validation ranks, eval).
