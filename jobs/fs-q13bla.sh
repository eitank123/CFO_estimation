#!/bin/bash
# fs-q13bla: FAST ID 13: blind, PROVISIONAL thresholds (F5 / spec off = best BLER, MACs upper bound; rho scaled), CFO U(+-0.03), seed 13 (paired with fs-q13pg / fs-q13da), 1e5 frames / 100 errors
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_blind_fs.py --fmt id13 --snrs -1.40 -1.20 -1.00 -0.80 --frames 100000 --max-err 100 --seed 13 --workers 16 --dump --part fs-q13bla
  echo "ALL DONE" ) > logs/run_fs-q13bla.out 2>&1
