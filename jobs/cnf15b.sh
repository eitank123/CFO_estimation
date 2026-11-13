#!/bin/bash
# cnf15b: 0.15 -2.5 / -2 dB 400k: nofast15 (new accounting, 2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py --max-frames 4000"
( $R --points 0.15:-2.5:100 0.15:-2:100 --rx nofast15 --seed 7702 --part t-cnf15b
  echo "ALL DONE" ) > logs/run_cnf15b.out 2>&1
