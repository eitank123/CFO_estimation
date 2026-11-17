#!/bin/bash
# fs-b13m06: blind ID 13 ONE point (Es/N0 -0.6), CFO U(+-0.03), provisional thresholds (early stops off), seed 13 batch 200 (paired with fs-q13pg / fs-q13da), 30 errors, per-packet dump
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_blind_fs.py --fmt id13 --snrs -0.6 --frames 20000 --max-err 30 --seed 13 --workers 16 --dump --part fs-b13m06
  echo "ALL DONE" ) > logs/run_fs-b13m06.out 2>&1
