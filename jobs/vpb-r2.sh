#!/bin/bash
# vpb-r2: few pilots N3x5 / V2x8 D32 / C24 + code search
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/2:2:4 1/2:2.5:4 1/2:3:4 1/2:3.5:4 1/2:4:4 --max-frames 25000 --min-errors 100 --rx "Pilots N3x5 + code search" "Pilots V2x8 D32 + code search" "Pilots C24 + code search" --seed 5413 --part vpb-r2 > logs/run_vpb-r2.out 2>&1
