#!/bin/bash
# ddq25: R experiments (dd, dd_win4) with q_fix vs base*_qfix, paired, at 2/5 and 1/2 (2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py --max-frames 4000"
( $R --points 2/5:0.5:16 2/5:1:16 --rx base25_qfix dd_qfix_25 dd_win4_qfix_25 --seed 7731 --part t-ddq25
  $R --points 1/2:2:16 1/2:2.5:16 --rx base2_qfix dd_qfix_2 dd_win4_qfix_2 --seed 7732 --part t-ddq2
  echo "ALL DONE" ) > logs/run_ddq25.out 2>&1
