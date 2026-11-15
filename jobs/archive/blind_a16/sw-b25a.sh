#!/bin/bash
# sw-b25a: in-cell CFO grid for the z-test (sub-grid 2 / in-cell retry), full sweep, paired with the final receivers
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 2/5:0.5:8 2/5:1:8 2/5:1.5:8 2/5:2:8 2/5:2.5:8 2/5:3:8 2/5:4:8 --max-frames 50000 --min-errors 100 --rx "v3 eco7, rescue, rho_n, sub-grid 2 + CRC" --seed 5702 --part sw-b25a > logs/run_sw-b25a.out 2>&1
