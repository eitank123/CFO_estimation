#!/bin/bash
# pv-r3b: pilots + v3 (pilot ruler in the posterior + pilot check of every CRC pass), points 1/3:0.5:4 1/3:1:4 1/3:1.5:4 1/3:2:4 1/3:2.5:4 1/3:3:4 
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/3:0.5:4 1/3:1:4 1/3:1.5:4 1/3:2:4 1/3:2.5:4 1/3:3:4  --max-frames 25000 --min-errors 100 --rx "Pilots N4x6 + v3 + CRC" "Pilots C24 + v3 + CRC" "Pilots N3x8 + v3, order only + CRC" "Pilots N3x8 + v3, check only + CRC" "Pilots N3x8 + v3 lite, adaptive + abort + CRC" --seed 5604 --part pv-r3b > logs/run_pv-r3b.out 2>&1
