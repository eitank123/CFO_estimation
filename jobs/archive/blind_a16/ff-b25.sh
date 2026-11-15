#!/bin/bash
# ff-b25: final-receiver fill (blind R=2/5 2.5-4 dB), paired seeds, completes the presented curves
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 2/5:2.5:8 2/5:3:8 2/5:4:8 --max-frames 50000 --min-errors 100 --rx "v3 eco7, rescue, rho_n + CRC" --seed 5702 --part ff-b25 > logs/run_ff-b25.out 2>&1
