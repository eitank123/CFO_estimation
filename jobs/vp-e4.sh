#!/bin/bash
# vp-e4: E4, comb pattern ranks + pilot-only ML outage / MSE
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_vp.py ranks --frames 2000 --chunks 4 --part a > logs/run_vp-e4.out 2>&1
