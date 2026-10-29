#!/bin/bash
# b25-f: blind / few-pilot BLER at R=2/5 (819 data bits), points 2/5:0.5:2 2/5:1:2 2/5:1.5:2 2/5:2:2 2/5:2.5:2 2/5:3:2 2/5:4:2
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 2/5:0.5:2 2/5:1:2 2/5:1.5:2 2/5:2:2 2/5:2.5:2 2/5:3:2 2/5:4:2 --max-frames 10000 --min-errors 100 --rx "Pilots N4x6 + code search" "Pilots N3x5 + code search" "Pilots V2x8 D32 + code search" "Pilots C24 + code search" "Pilots N4x4 + blind terms + code search" --seed 5506 --part b25-f > logs/run_b25-f.out 2>&1
