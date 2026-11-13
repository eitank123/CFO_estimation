#!/bin/bash
# dec-smoke: smoke: decode dump on/off identity, q_fix=False identity, q_fix effect at 2-phase points (2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u BLIND_IMPLEMENTATION/testing/run.py --points 0.15:-4.5:4 --rx nofast15 nofast15_dump nofast15_qfix --max-frames 25 --seed 7898 --part t-dec-smoke-a
  $PY -u BLIND_IMPLEMENTATION/testing/run.py --points 2/5:0:4 --rx base25 base25_dump base25_qfix base25_qfix_dump --max-frames 25 --seed 7898 --part t-dec-smoke-b
  $PY -u BLIND_IMPLEMENTATION/testing/run.py --points 1/10:-1:4 --rx base10 base10_qfix --max-frames 25 --seed 7898 --part t-dec-smoke-c
  echo "ALL DONE" ) > logs/run_dec-smoke.out 2>&1
