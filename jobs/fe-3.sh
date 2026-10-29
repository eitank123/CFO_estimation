#!/bin/bash
# fe-3: E3, reliability-weighted node metric (LDA / detector-aligned / MLP) vs the plain path metric
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_fast.py weights --rates 1/10 1/4 1/2 --frames 1000 --chunks 4 --part a > logs/run_fe-3.out 2>&1
