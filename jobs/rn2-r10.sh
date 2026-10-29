#!/bin/bash
# rn2-r10: rank NN on the default grid, blind R = 1/10 (paired with eco6 / eco7)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/10:-3:8 1/10:-2:8 1/10:-1:8 1/10:0:8 --max-frames 50000 --min-errors 100 --rx "v3 eco7, rank NN, default grid + CRC" --seed 5701 --part rn2-r10 > logs/run_rn2-r10.out 2>&1
