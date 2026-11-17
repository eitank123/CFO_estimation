#!/bin/bash
# tw15b: testing_s11g, 0.15 -2.5 dB 480k + the missing -5, -4.5 dB at 64k (2026-11-15; testing model over the full SNR range, user request)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py --max-frames 4000"
( $R --points 0.15:-2.5:120 0.15:-5:16 0.15:-4.5:16 --rx testing_s11g --seed 8204 --part t-tw15b
  echo "ALL DONE" ) > logs/run_tw15b.out 2>&1
