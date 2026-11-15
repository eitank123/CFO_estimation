#!/bin/bash
# b10la: blind testing receiver (testing_s11g) R = 1/10 at -5.5 dB, 64k (presentation waterfall extension, 2026-11-16)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( $R --max-frames 4000 --seed 7980 --points 1/10:-5.5:16 --rx testing_s11g --part t-b10la
  echo "ALL DONE" ) > logs/run_b10la.out 2>&1
