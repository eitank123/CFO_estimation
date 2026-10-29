#!/bin/bash
# m9-r10: 24 pilots, eco7 without grid 6 (screening from -3.5 dB only), R = 1/10, paired (seed 5701)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/10:-5:8 1/10:-4:8 1/10:-3:8 1/10:-2:8 1/10:-1:8 1/10:0:8 --max-frames 50000 --min-errors 100 --rx "Pilots N3x8 + v3 eco7, default grid + CRC" --seed 5701 --part m9-r10 > logs/run_m9-r10.out 2>&1
