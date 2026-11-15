#!/bin/bash
# nnb-smoke: smoke of the retry gate (nn_b) at high-BLER points (2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py --max-frames 25 --seed 7898"
( $R --points 0.15:-4.5:4 1/10:-5.5:4 --rx nofast15_qfix nofast15_qfix_nnb1 nofast15_qfix_nnb01 --part t-nnb-smoke-a
  $R --points 2/5:0:4 --rx base25_qfix base25_qfix_nnb1 base25_qfix_nnb01 --part t-nnb-smoke-b
  $R --points 1/2:1.5:4 --rx base2_qfix base2_qfix_nnb1 --part t-nnb-smoke-c
  echo "ALL DONE" ) > logs/run_nnb-smoke.out 2>&1
