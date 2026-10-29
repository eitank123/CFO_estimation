#!/bin/bash
# rh-b10a: rescue + the normalised re-encoding check rho_n (staircase false passes), paired with the rescue / eco runs
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/10:-5:8 --max-frames 25000 --min-errors 100 --rx "v3 eco7, rescue, rho_n + CRC" --seed 5701 --part rh-b10a > logs/run_rh-b10a.out 2>&1
