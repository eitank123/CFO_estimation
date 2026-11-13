#!/bin/bash
# cnf10b: 1/10 -4.5 / -4 dB 400k: nofast15 (new accounting, 2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py --max-frames 4000"
( $R --points 1/10:-4.5:100 1/10:-4:100 --rx nofast15 --seed 7701 --part t-cnf10b
  echo "ALL DONE" ) > logs/run_cnf10b.out 2>&1
