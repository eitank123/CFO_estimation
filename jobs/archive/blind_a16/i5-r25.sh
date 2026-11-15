#!/bin/bash
# i5-r25: eco5 = the best blind / 24-pilot receivers of the MAC cycle, paired with the earlier runs (same seed)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 2/5:0.5:8 2/5:1:8 2/5:1.5:8 2/5:2:8 2/5:2.5:8 2/5:3:8 2/5:4:8 --max-frames 50000 --min-errors 100 --rx "v3 eco5 + CRC" "Pilots N3x8 + v3 eco5 + CRC" --seed 5702 --part i5-r25 > logs/run_i5-r25.out 2>&1
