#!/bin/bash
# vpc-r3: few pilots: other patterns, blind terms, 4th-power phase, R = 1/3
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/3:0.5:2 1/3:1:2 1/3:1.5:2 1/3:2:2 1/3:2.5:2 1/3:3:2 1/3:2:2 --max-frames 10000 --min-errors 100 --rx "Pilots N4x6 + code search" "Pilots R3x8 + code search" "Pilots V2x8 D64 + code search" "Pilots N4x4 + blind terms + code search" "Pilots C16 + blind terms + code search" "Pilots N4x4 + code search, 4th-power phase" "Pilots N3x8 + code search, 4th-power phase" --seed 5463 --part vpc-r3 > logs/run_vpc-r3.out 2>&1
