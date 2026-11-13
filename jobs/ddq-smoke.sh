#!/bin/bash
# ddq-smoke: smoke of the R experiments with q_fix (dd_qfix_*, dd_win4_qfix_*, dd_qfix) (2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py --max-frames 25 --seed 7897"
( $R --points 2/5:0:4 --rx base25_qfix dd_qfix_25 dd_win4_qfix_25 --part t-ddq-smoke-a
  $R --points 1/2:1.5:4 --rx base2_qfix dd_qfix_2 dd_win4_qfix_2 --part t-ddq-smoke-b
  $R --points 0.15:-1:4 --rx base10_qfix dd_qfix dd_win4_qfix --part t-ddq-smoke-c
  echo "ALL DONE" ) > logs/run_ddq-smoke.out 2>&1
