#!/bin/bash
# h1-id2-p100-h2 (2026-11-25, H2 = h1 all, ID 2 screen, sync_cfo/expected_fs.md "H1 step 1 (ID 2)"): Es/N0 1.0 dB, 200000 packets,
# the exact fin-id2-twc args (seed 7052: the SAME packets as h1-id2-a-p100 / fin-id2-twc-p100), --dump-lite --lite-ops, no
# max-err stop; arm E2: NO separate fast path, the combined Y4 + Y2 top-K local direct decode on every packet, then the
# unchanged stages 2-5, at K 8 with M 1 and M 2 (C2 = E2's H1 part, derived offline); no LS on ID 2. est. wall time ~5 min
cd "$(dirname "$(readlink -f "$0")")/.."
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo BLIND_MAC_UNIT=ops
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs results
CF="--crc 24 --batch 200 --sub 50 --beta 0.2 --cfo-max 0.03 --rho fmt --spec off --cknn fmt --cknn-name ck_nn_fs_id2w_twc --ck useful --bpsk-phase sq --design ga --charge-all --dump-lite --lite-ops --workers 16"
FIN='"final": 4, "win": 4.5, "ck_keep": 0.007, "ck_min": 4, "kmin": 8, "vv_p": 2, "tw_ph": "iv"'
AF="--list 16 --fmt id2 --seed 7052 --design-snr 0.8 --fzstop 0.55,0.77 --max-err 1000000000 --twin search:k12:rd --twin-fe jt --snrs 1.0 --frames 200000"
H='"K": 8, "union": false, "w": [1.0, 1.0, 1.0], "ls": null, "fb": true, "all": true'
( $PY -u run_blind_fs.py $CF $AF --sps "{$FIN, \"h1\": {$H, \"M\": 1}}" --part h1-id2-e2-p100-m1
  $PY -u run_blind_fs.py $CF $AF --sps "{$FIN, \"h1\": {$H, \"M\": 2}}" --part h1-id2-e2-p100-m2
  echo "ALL DONE" ) > logs/run_h1-id2-p100-h2.out 2>&1
