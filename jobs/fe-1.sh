#!/bin/bash
# fe-1: E1, rank of the true CFO cell under the coarse posteriors (blind_fast.py coarse)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results
$PY -u blind_fast.py coarse --frames 10000 --chunks 4 --part a > logs/run_fe-1.out 2>&1
