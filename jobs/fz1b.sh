#!/bin/bash
# fz1b: frozen-bit diagnostic (fz_diag, log-only; the _fz arm only), R = 0.15 -4 dB, 16k packets (half of 32k) (2026-11-16, expected_f3f5.md F5)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( $R --max-frames 1000 --seed 8025 --points 0.15:-4:16 --rx testing_s11g_fz --part t-fz1b
  echo "ALL DONE" ) > logs/run_fz1b.out 2>&1
