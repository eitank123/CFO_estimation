#!/bin/bash
# ff-p10: final-receiver fill (pilots R=1/10 -3 dB), paired seeds, completes the presented curves
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/10:-3:8 --max-frames 50000 --min-errors 100 --rx "Pilots N3x8 + v3 eco7, rescue, rho_n + CRC" --seed 5701 --part ff-p10 > logs/run_ff-p10.out 2>&1
