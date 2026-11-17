#!/bin/bash
# fs-q13pg: FAST ID 13 first plot: polar genie L 8 (paired with fs-pg13 / fs-rcs2v13 seed 13), 3e5 frames / 100 errors per point
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_polar_genie.py --fmt id13 --snrs -1.40 -1.20 -1.00 -0.80 -0.60 -0.40 -0.20 --frames 300000 --max-err 100 --seed 13 --workers 16 --part fs-q13pg
  echo "ALL DONE" ) > logs/run_fs-q13pg.out 2>&1
