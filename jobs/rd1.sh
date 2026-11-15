#!/bin/bash
# rd1: Stage 3 refinement diagnostic (ref_diag, log-only; base + _rd on the same packets), R = 1/10 -5 dB, 0.15 -4 / -3 dB, 8k packets per point (2026-11-15, expected_ref.md D0)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( $R --max-frames 500 --seed 8012 --points 1/10:-5:16 0.15:-4:16 0.15:-3:16 --rx testing_s11g testing_s11g_rd --part t-rd1
  echo "ALL DONE" ) > logs/run_rd1.out 2>&1
