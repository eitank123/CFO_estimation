#!/bin/bash
# fz2a: frozen-bit diagnostic (fz_diag, log-only; the _fz arm only), R = 2/5 0.5 dB, 16k packets (half of 32k) (2026-11-16, expected_f3f5.md F5)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( $R --max-frames 1000 --seed 8026 --points 2/5:0.5:16 --rx base25_qfix_fz --part t-fz2a
  echo "ALL DONE" ) > logs/run_fz2a.out 2>&1
