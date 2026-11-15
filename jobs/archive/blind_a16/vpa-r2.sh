#!/bin/bash
# vpa-r2: few pilots N3x8 / N4x4 / C16 + code search, BLER + MACs + CFO outage
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/2:2:4 1/2:2.5:4 1/2:3:4 1/2:3.5:4 1/2:4:4 --max-frames 25000 --min-errors 100 --rx "Pilots N3x8 + code search" "Pilots N4x4 + code search" "Pilots C16 + code search" --seed 5403 --part vpa-r2 > logs/run_vpa-r2.out 2>&1
