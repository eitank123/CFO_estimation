#!/bin/bash
# rh-b10b: rescue + the normalised re-encoding check rho_n (staircase false passes), paired with the rescue / eco runs
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/10:-4:8 1/10:-3:8 1/10:-2:8 1/10:-1:8 1/10:0:8 --max-frames 50000 --min-errors 100 --rx "v3 eco7, rescue, rho_n + CRC" --seed 5701 --part rh-b10b > logs/run_rh-b10b.out 2>&1
