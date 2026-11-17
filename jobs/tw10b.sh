#!/bin/bash
# tw10b: testing_s11g, 1/10 -4 dB 480k and -3.5 dB 256k (2026-11-15; testing model over the full SNR range, user request)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py --max-frames 4000"
( $R --points 1/10:-4:120 1/10:-3.5:64 --rx testing_s11g --seed 8202 --part t-tw10b
  echo "ALL DONE" ) > logs/run_tw10b.out 2>&1
