#!/bin/bash
# h1-id13-e2l-m09 (2026-11-25, H2 = arm e2l (combined spectrum on every packet, cell LS FFT, fallback) at the extra SNR point
# -0.9 dB; same args as h1-id13-e2l-m08, same seed 9913 / packets as h1-id13-a-m09 / h1-id13-e-m09; dump-lite like those)
cd "$(dirname "$(readlink -f "$0")")/.."
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo BLIND_MAC_UNIT=ops
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs results
C="--crc 24 --batch 200 --sub 50 --beta 0.2 --cfo-max 0.03 --rho scaled --spec off --cknn fmt --ck useful --bpsk-phase sq --design ga --charge-all --dump-lite --lite-ops --workers 16"
B='"final": 16, "win": 4.5, "ck_keep": 0.003, "ck_min": 8, "vv_p": 2, "tw_ph": "iv"'
S_X='{'"$B"', "h1": {"K": 8, "M": 1, "union": false, "fb": true, "all": true, "ls": "data/dual_w4_id13_twc.json", "ls_L": "cell"}}'
( $PY -u run_blind_fs.py $C --list 16 --fmt id13 --seed 9913 --design-snr -0.5 --fzstop 0.6,0.80 --max-err 1000000000 --sps "$S_X" --twin search:k18:rd --twin-fe jt --snrs -0.9 --frames 16000 --part h1-id13-e2l-m09
  echo "ALL DONE" ) > logs/run_h1-id13-e2l-m09.out 2>&1
