#!/bin/bash
# id2x-e2-p040b (2026-11-25, user-approved): ID 2 arm e2 at 0.4 dB, seed 7052, chunks 50..99 of 40000 packets (part 2/4),
# exact config of h1-id2-p050-h2.sh (e2, M 1) / h1-id2-p050-e.sh (a); part h1-id2-e2-p040b-m1. Submitted directly (no worker pool).
cd "$(dirname "$(readlink -f "$0")")/.."
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo BLIND_MAC_UNIT=ops
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs results
CF="--crc 24 --batch 200 --sub 50 --beta 0.2 --cfo-max 0.03 --rho fmt --spec off --cknn fmt --cknn-name ck_nn_fs_id2w_twc --ck useful --bpsk-phase sq --design ga --charge-all --dump-lite --lite-ops --workers 16"
FIN='"final": 4, "win": 4.5, "ck_keep": 0.007, "ck_min": 4, "kmin": 8, "vv_p": 2, "tw_ph": "iv"'
AF="--list 16 --fmt id2 --seed 7052 --design-snr 0.8 --fzstop 0.55,0.77 --max-err 1000000000 --twin search:k12:rd --twin-fe jt --snrs 0.4 --frames 40000 --chunks 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99"
H='"K": 8, "union": false, "w": [1.0, 1.0, 1.0], "ls": null, "fb": true, "all": true'
( $PY -u run_blind_fs.py $CF $AF --sps "{$FIN, \"h1\": {$H, \"M\": 1}}" --part h1-id2-e2-p040b-m1
  echo "ALL DONE" ) > logs/run_id2x-e2-p040b.out 2>&1
