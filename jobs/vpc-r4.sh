#!/bin/bash
# vpc-r4: few pilots: other patterns, blind terms, 4th-power phase
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/4:0:2 1/4:0.5:2 1/4:1:2 1/4:1.5:2 1/4:2:2 1/4:3:2 --max-frames 10000 --min-errors 100 --rx "Pilots N4x6 + code search" "Pilots R3x8 + code search" "Pilots V2x8 D64 + code search" "Pilots N4x4 + blind terms + code search" "Pilots C16 + blind terms + code search" "Pilots N4x4 + code search, 4th-power phase" "Pilots N3x8 + code search, 4th-power phase" --seed 5422 --part vpc-r4 > logs/run_vpc-r4.out 2>&1
