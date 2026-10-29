#!/bin/bash
# i5-r10: eco5 at R = 1/10 (blind gated; 24 pilots with / without the pilot-chosen search phases from -4.5 dB), paired (seed 5701)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/10:-5:8 1/10:-4:8 1/10:-3:8 1/10:-2:8 1/10:-1:8 1/10:0:8 --max-frames 50000 --min-errors 100 --rx "v3 eco5 + CRC" "Pilots N3x8 + v3 eco5 + CRC" "Pilots N3x8 + v3 eco5, pilot phase + CRC" --seed 5701 --part i5-r10 > logs/run_i5-r10.out 2>&1
