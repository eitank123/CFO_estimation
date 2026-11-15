#!/bin/bash
# fz3: frozen-bit diagnostic (fz_diag, log-only; the _fz arm only), R = 1/10 -5 dB, 1/2 2 dB, 8k packets per point (2026-11-16, expected_f3f5.md F5)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( $R --max-frames 500 --seed 8028 --points 1/10:-5:16 --rx testing_s11g_fz --part t-fz3a
  $R --max-frames 500 --seed 8028 --points 1/2:2:16 --rx base2_qfix_fz --part t-fz3b
  echo "ALL DONE" ) > logs/run_fz3.out 2>&1
