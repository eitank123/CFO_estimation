#!/bin/bash
# sg-p2: in-cell CFO grid for the z-test at R = 1/10, -5 dB, paired with the final receiver (seed 5701)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/10:-5:8 --max-frames 50000 --min-errors 100 --rx "Pilots N3x8 + v3 eco7, rescue, rho_n, fast R=1/10 from -2 dB, in-cell retry + CRC" --seed 5701 --part sg-p2 > logs/run_sg-p2.out 2>&1
