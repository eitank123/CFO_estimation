#!/bin/bash
# id2x-e2-p040d (2026-11-25, user-approved): ID 2 arm e2 at 0.4 dB, seed 7052, chunks 150..199 of 40000 packets (part 4/4),
# exact config of h1-id2-p050-h2.sh (e2, M 1) / h1-id2-p050-e.sh (a); part h1-id2-e2-p040d-m1. Submitted directly (no worker pool).
cd "$(dirname "$(readlink -f "$0")")/.."
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo BLIND_MAC_UNIT=ops
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs results
CF="--crc 24 --batch 200 --sub 50 --beta 0.2 --cfo-max 0.03 --rho fmt --spec off --cknn fmt --cknn-name ck_nn_fs_id2w_twc --ck useful --bpsk-phase sq --design ga --charge-all --dump-lite --lite-ops --workers 16"
FIN='"final": 4, "win": 4.5, "ck_keep": 0.007, "ck_min": 4, "kmin": 8, "vv_p": 2, "tw_ph": "iv"'
AF="--list 16 --fmt id2 --seed 7052 --design-snr 0.8 --fzstop 0.55,0.77 --max-err 1000000000 --twin search:k12:rd --twin-fe jt --snrs 0.4 --frames 40000 --chunks 150 151 152 153 154 155 156 157 158 159 160 161 162 163 164 165 166 167 168 169 170 171 172 173 174 175 176 177 178 179 180 181 182 183 184 185 186 187 188 189 190 191 192 193 194 195 196 197 198 199"
H='"K": 8, "union": false, "w": [1.0, 1.0, 1.0], "ls": null, "fb": true, "all": true'
( $PY -u run_blind_fs.py $CF $AF --sps "{$FIN, \"h1\": {$H, \"M\": 1}}" --part h1-id2-e2-p040d-m1
  echo "ALL DONE" ) > logs/run_id2x-e2-p040d.out 2>&1
