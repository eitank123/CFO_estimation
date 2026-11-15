#!/bin/bash
# sg-b2: in-cell CFO grid for the z-test at R = 1/10, -5 dB, paired with the final receiver (seed 5701)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/10:-5:8 --max-frames 25000 --min-errors 100 --rx "v3 eco7, rescue, rho_n, in-cell retry + CRC" --seed 5701 --part sg-b2 > logs/run_sg-b2.out 2>&1
