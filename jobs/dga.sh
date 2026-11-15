#!/bin/bash
# dga: decode dumps at more SNRs for the retry gate (1/10, 0.15) (2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( $R --max-frames 4000 --seed 7791 --points 1/10:-5.5:8 1/10:-4.5:8 0.15:-4.5:8 0.15:-3.5:8 --rx nofast15_qfix_dump --part t-dga
  echo "ALL DONE" ) > logs/run_dga.out 2>&1
