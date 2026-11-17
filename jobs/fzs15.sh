#!/bin/bash
# fzs15: F5 online (fzstop q 0.9, t 0.763) vs testing_s11g on the same packets, R = 0.15 -4 dB, 16 x 4000 = 64k (2026-11-15, expected_f3f5.md F5 online)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( $R --max-frames 4000 --seed 8046 --points 0.15:-4:16 --rx testing_s11g testing_s11g_fzs --part t-fzs15 
  echo "ALL DONE" ) > logs/run_fzs15.out 2>&1
