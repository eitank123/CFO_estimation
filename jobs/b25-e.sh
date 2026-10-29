#!/bin/bash
# b25-e: blind / few-pilot BLER at R=2/5 (819 data bits), points 2/5:0.5:4 2/5:1:4 2/5:1.5:4 2/5:2:4 2/5:2.5:4 2/5:3:4 2/5:4:4
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 2/5:0.5:4 2/5:1:4 2/5:1.5:4 2/5:2:4 2/5:2.5:4 2/5:3:4 2/5:4:4 --max-frames 25000 --min-errors 100 --rx "Pilots N3x8 + code search" "Pilots N4x4 + code search" "Pilots C16 + code search" --seed 5505 --part b25-e > logs/run_b25-e.out 2>&1
