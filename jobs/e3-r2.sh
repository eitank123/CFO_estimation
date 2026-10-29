#!/bin/bash
# e3-r2: eco3+ blind and pilots N3x8 + eco3+, paired with ep-r2 / pe-r2
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/2:2:8 1/2:2.5:8 1/2:3:8 1/2:3.5:8 1/2:4:8 1/2:5:8 --max-frames 50000 --min-errors 100 --rx "v3 eco3+ + CRC" "Pilots N3x8 + v3 eco3+ + CRC" --seed 5703 --part e3-r2 > logs/run_e3-r2.out 2>&1
