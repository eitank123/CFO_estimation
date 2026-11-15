#!/bin/bash
# sw-p10: in-cell CFO grid for the z-test (sub-grid 2 / in-cell retry), full sweep, paired with the final receivers
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/10:-4:8 1/10:-3:8 1/10:-2:8 1/10:-1:8 1/10:0:8 --max-frames 50000 --min-errors 100 --rx "Pilots N3x8 + v3 eco7, rescue, rho_n, fast R=1/10 from -2 dB, sub-grid 2 + CRC" "Pilots N3x8 + v3 eco7, rescue, rho_n, fast R=1/10 from -2 dB, in-cell retry + CRC" --seed 5701 --part sw-p10 > logs/run_sw-p10.out 2>&1
