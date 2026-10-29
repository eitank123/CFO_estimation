#!/bin/bash
# l8-r10c: eco8 candidate, 24 pilots R = 1/10: pilot-picked fast path from -1 dB
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/10:-1:8 1/10:0:8 --max-frames 50000 --min-errors 100 --rx "Pilots N3x8 + v3 eco7, fast path R=1/10 from -1 dB + CRC" --seed 5701 --part l8-r10c > logs/run_l8-r10c.out 2>&1
