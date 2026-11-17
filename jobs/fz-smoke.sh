#!/bin/bash
# fz-smoke: smoke of the frozen-bit diagnostic (small_rx fz_diag, log-only; base + _fz on the same packets), 400 packets per point, R = 0.15 -4 dB, 2/5 0.5 dB (2026-11-15, expected_f3f5.md F5)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( $R --max-frames 100 --seed 8021 --points 0.15:-4:4 --rx testing_s11g testing_s11g_fz --part t-fz-smoke-a
  $R --max-frames 100 --seed 8021 --points 2/5:0.5:4 --rx base25_qfix base25_qfix_fz --part t-fz-smoke-b
  echo "ALL DONE" ) > logs/run_fz-smoke.out 2>&1
