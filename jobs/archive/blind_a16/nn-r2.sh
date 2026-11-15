#!/bin/bash
# nn-r2: NN peak grader in the fast path, R = 1/2 (blind, 24 pilots)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/2:2:8 1/2:2.5:8 1/2:3:8 1/2:3.5:8 1/2:4:8 1/2:5:8 --max-frames 50000 --min-errors 100 --rx "v3 eco7, NN peak + CRC" "Pilots N3x8 + v3 eco7, NN peak + CRC" --seed 5703 --part nn-r2 > logs/run_nn-r2.out 2>&1
