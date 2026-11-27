#!/bin/bash
# (2026-11-25, ls_L variant of h1-id13-e2-m08: the SAME args / seed 9913 / packets + h1 "ls_L": "cell" = the receiver-cell LS FFT,
# L = 16384 (bin 6.1e-5 <= the k 2 STEP cell 1.04e-4; 4096 would be 2.3 cells), |D| folded mod L, linearly
# interpolated for the peak pick, cells re-scored by the exact LS DTFT (ls_rs); paired with h1-id13-e2-m08 for the coverage check)
# h1-id13-e2l-m08 (2026-11-25, H1 step 1 screen, ID 13, sync_cfo/expected_fs.md "H1 step 1 (ID 13)"): arm e2, Es/N0 -0.8 dB, 20000 packets (chunks 0..99), full dump
# Baseline A = the exact twc-id13-ph args (18 moved bits search:k18:rd, CRC-24, L 16, twin phase tw_ph iv, ck NN ck_nn_fs_id13,
# --cknn fmt) on HELD-OUT seed 9913 (unused before), batch 200; all arms on the SAME packets (same seed, snr, chunks).
# H1_FLAGS_<arm> = placeholder for the main builder's small_rx sps key "h1" (H1_DEF keys); replace the token by the text
# below (leading comma, inside the sps JSON) before submission; the guard refuses an unfilled token. K / M: from the
# fast-path-failure coverage of the calibration packets (h1_step0_id13.md; design 2026-11-25 K 8, M 1), combined score only:
#   H1_FLAGS_C0 -> , "h1": {"K": 8, "M": 1, "union": false, "fb": false, "ls": null}             (Y4 + Y2 only, local only)
#   H1_FLAGS_C  -> , "h1": {"K": 8, "M": 1, "union": false, "fb": false, "ls": "data/dual_w4_id13_twc.json"}   (Y4 + Y2 + LS)
#   H1_FLAGS_E  -> , "h1": {"K": 8, "M": 1, "union": false, "fb": true, "ls": "data/dual_w4_id13_twc.json"}    (C + fallback)
#   H1_FLAGS_C2 -> , "h1": {"K": 8, "M": 1, "union": false, "fb": false, "all": true, "ls": "data/dual_w4_id13_twc.json"}   (no fast path)
#   H1_FLAGS_E2 -> , "h1": {"K": 8, "M": 1, "union": false, "fb": true, "all": true, "ls": "data/dual_w4_id13_twc.json"}    (C2 + fallback)
#   H1_FLAGS_PKLOG -> , "pk_w4": "data/dual_w4_id13_twc.json", "h1": {"K": 8, "M": 2, "union": false, "fb": true, "ls": "data/dual_w4_id13_twc.json"}
# needs jobs/h1-id13-prep.sh (or the local export, 2026-11-25) for the LS json (arms C / E / C2 / E2 / pk)
# est. wall time ~6-9 min; disk ~40 MB
cd "$(dirname "$(readlink -f "$0")")/.."
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo BLIND_MAC_UNIT=ops
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs results
C="--crc 24 --batch 200 --sub 50 --beta 0.2 --cfo-max 0.03 --rho scaled --spec off --cknn fmt --ck useful --bpsk-phase sq --design ga --charge-all --dump --workers 16"
B='"final": 16, "win": 4.5, "ck_keep": 0.003, "ck_min": 8, "vv_p": 2, "tw_ph": "iv"'
S_E2='{'"$B"', "h1": {"K": 8, "M": 1, "union": false, "fb": true, "all": true, "ls": "data/dual_w4_id13_twc.json", "ls_L": "cell"}}'
( for s_ in "$S_E2"; do case "$s_" in *H1_FLAGS*) echo "FAILED: H1_FLAGS placeholder not filled: $s_"; exit 2;; esac; done
  $PY -u run_blind_fs.py $C --list 16 --fmt id13 --seed 9913 --design-snr -0.5 --fzstop 0.6,0.80 --max-err 1000000000 --sps "$S_E2" --twin search:k18:rd --twin-fe jt --snrs -0.8 --frames 20000 --part h1-id13-e2l-m08
  echo "ALL DONE" ) > logs/run_h1-id13-e2l-m08.out 2>&1
