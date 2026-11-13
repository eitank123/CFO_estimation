#!/bin/bash
# ddq10: R experiments (dd, dd_win4) with q_fix vs base10_qfix, paired, at the 2-phase points of 1/10 and 0.15 (2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py --max-frames 4000"
( $R --points 1/10:-1:16 0.15:-1:16 0.15:0:16 --rx base10_qfix dd_qfix dd_win4_qfix --seed 7733 --part t-ddq10
  echo "ALL DONE" ) > logs/run_ddq10.out 2>&1
