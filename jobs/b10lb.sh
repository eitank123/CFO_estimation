#!/bin/bash
# b10lb: blind testing receiver (testing_s11g) R = 1/10 at -6.0 dB, 64k (presentation waterfall extension, 2026-11-16)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( $R --max-frames 4000 --seed 7981 --points 1/10:-6.0:16 --rx testing_s11g --part t-b10lb
  echo "ALL DONE" ) > logs/run_b10lb.out 2>&1
