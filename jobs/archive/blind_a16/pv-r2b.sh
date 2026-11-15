#!/bin/bash
# pv-r2b: pilots + v3 (pilot ruler in the posterior + pilot check of every CRC pass), points 1/2:2:4 1/2:2.5:4 1/2:3:4 1/2:3.5:4 1/2:4:4 1/2:5:4 
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/2:2:4 1/2:2.5:4 1/2:3:4 1/2:3.5:4 1/2:4:4 1/2:5:4  --max-frames 25000 --min-errors 100 --rx "Pilots N4x6 + v3 + CRC" "Pilots C24 + v3 + CRC" "Pilots N3x8 + v3, order only + CRC" "Pilots N3x8 + v3, check only + CRC" "Pilots N3x8 + v3 lite, adaptive + abort + CRC" --seed 5608 --part pv-r2b > logs/run_pv-r2b.out 2>&1
