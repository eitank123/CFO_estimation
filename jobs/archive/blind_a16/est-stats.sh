#!/bin/bash
# est-stats: estimation statistics of the current receiver stages for the coarse/ and estimation/ figures
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/results
$PY -u blind/smoke/est_stats.py --frames 4000 > logs/run_est-stats.out 2>&1
