#!/bin/bash
# dec-b: decode dump 32k: 2/5 0.5, 1/2 2 dB (q_fix); noise-only 0.15 -1 dB 5.6k (2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py --max-frames 4000"
( $R --points 2/5:0.5:8 --rx base25_qfix_dump --seed 7722 --part t-decb25
  $R --points 1/2:2:8 --rx base2_qfix_dump --seed 7723 --part t-decb2
  $PY -u BLIND_IMPLEMENTATION/testing/run.py --points 0.15:-1:8 --rx nofast15_dump --max-frames 625 --noise-only --seed 7724 --part t-decbn
  echo "ALL DONE" ) > logs/run_dec-b.out 2>&1
