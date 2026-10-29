#!/bin/bash
# pf2-r10: the 24-pilot fast path at R = 1/10 from -2 dB with the rho_n check + rescue (paired with fx3-r10p / m9-r10)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/10:-2:8 1/10:-1:8 1/10:0:8 --max-frames 50000 --min-errors 100 --rx "Pilots N3x8 + v3 eco7, rescue, rho_n, fast R=1/10 from -2 dB + CRC" --seed 5701 --part pf2-r10 > logs/run_pf2-r10.out 2>&1
