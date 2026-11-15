#!/bin/bash
# sw-b2: in-cell CFO grid for the z-test (sub-grid 2 / in-cell retry), full sweep, paired with the final receivers
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/2:2:8 1/2:2.5:8 1/2:3:8 1/2:3.5:8 1/2:4:8 1/2:5:8 --max-frames 50000 --min-errors 100 --rx "v3 eco7, rescue, rho_n, sub-grid 2 + CRC" "v3 eco7, rescue, rho_n, in-cell retry + CRC" --seed 5703 --part sw-b2 > logs/run_sw-b2.out 2>&1
