#!/bin/bash
# dec-a: decode dump 32k: 1/10 -5, 0.15 -4 / -3 dB (nofast15) (2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py --max-frames 4000"
( $R --points 1/10:-5:8 0.15:-4:8 0.15:-3:8 --rx nofast15_dump --seed 7721 --part t-deca
  echo "ALL DONE" ) > logs/run_dec-a.out 2>&1
