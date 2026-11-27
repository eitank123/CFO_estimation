#!/bin/bash
# h1-id3-e2l-m02 (2026-11-25, H2 cell-FFT variant of the H1 / H2 step 1 screen ID 3, arm E2 + h1 "ls_L": "cell"): Es/N0 -0.2 dB,
# 60000 packets, the SAME packets as h1-id3-e2-m02 (HELD-OUT seed 9903, batch 200, same chunk entropy / packet index; paired for
# the coverage check). "ls_L": "cell" = the receiver-cell LS FFT (ID 3 default L = 4 nf = 8192; "cell" = the smallest power of 2
# with a bin <= the search cell k STEP), |D| folded mod L, linearly interpolated for the peak pick, cells re-scored by the exact
# LS DTFT (ls_rs, H1_DEF default true). --dump-lite --lite-ops. est. wall ~2-4 min (the E2 arm took 55 s); disk ~6 MB
# Baseline A = the exact tz0-id3 args (18 moved bits --twin search:k18z0:rd, z0 arrangement, CRC-24, L 16, twin phase tw_ph iv,
# --twin-fe jt, ck NN ck_nn_fs_id3_c3 via --cknn fmt, --rho scaled, fzstop off, design-snr 0.0, sps final 8 / win 4.5 / vv_p 2),
# no early stop (max-err 1e9). NO repeated twins. H line = the H1 ID 3 screen (K 8, M 1, union off, w (1, 1, 1)).
#   C2 : h1 all (H2: no fast path), ends        E2 : C2 + the fallback
# LS = data/dual_w4_id3_tz0.json (push it with the code, or run jobs/h1-id3-prep.sh first).
cd "$(dirname "$(readlink -f "$0")")/.."
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo BLIND_MAC_UNIT=ops
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs results
LS=data/dual_w4_id3_tz0.json
C="--crc 24 --batch 200 --sub 50 --beta 0.2 --cfo-max 0.03 --rho scaled --spec off --cknn fmt --ck useful --bpsk-phase sq --design ga --charge-all --workers 16"
AF="--list 16 --fmt id3 --design-snr 0.0 --fzstop off --max-err 1000000000 --twin search:k18z0:rd --twin-fe jt"
B='"final": 8, "win": 4.5, "vv_p": 2, "tw_ph": "iv"'
H='"K": 8, "M": 1, "union": false, "w": [1.0, 1.0, 1.0]'
S_X="{$B, \"h1\": {$H, \"fb\": true, \"all\": true, \"ls\": \"$LS\", \"ls_L\": \"cell\"}}"
run() { $PY -u run_blind_fs.py $C $AF "$@" || echo "FAILED: run_blind_fs $*"; }
( date
  test -s $LS || { echo "FAILED: $LS missing (push it, or run jobs/h1-id3-prep.sh)"; exit 2; }
  run --seed 9903 --snrs -0.2 --frames 60000 --dump-lite --lite-ops --sps "$S_X" --part h1-id3-e2l-m02
  date
  echo "ALL DONE" ) > logs/run_h1-id3-e2l-m02.out 2>&1
