#!/bin/bash
# srch-smoke: smoke: search experiments R1-R3 (baseline, dd, win4, dd_win4, dd_k6), paired
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u BLIND_IMPLEMENTATION/testing/run.py --points 1/10:-5:1 0.15:-1:1 --rx base10 dd win4 dd_win4 dd_k6 --max-frames 64 --seed 7799 --part srch-smoke
  echo "ALL DONE" ) > logs/run_srch-smoke.out 2>&1
