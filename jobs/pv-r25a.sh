#!/bin/bash
# pv-r25a: pilots + v3 (pilot ruler in the posterior + pilot check of every CRC pass), points 2/5:0.5:8 2/5:1:8 2/5:1.5:8 2/5:2:8 2/5:2.5:8 2/5:3:8 2/5:4:8 
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 2/5:0.5:8 2/5:1:8 2/5:1.5:8 2/5:2:8 2/5:2.5:8 2/5:3:8 2/5:4:8  --max-frames 50000 --min-errors 100 --rx "Pilots N3x8 + v3 + CRC" "Pilots N4x4 + v3 + CRC" "Pilots C16 + v3 + CRC" --seed 5605 --part pv-r25a > logs/run_pv-r25a.out 2>&1
