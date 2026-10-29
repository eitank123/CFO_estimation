#!/bin/bash
# sg-smoke: in-cell CFO grid receivers run + MACs (smoke, BLER not meaningful)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/10:-5:8 2/5:0.5:8 --max-frames 250 --min-errors 100 --rx "v3 eco7, rescue, rho_n + CRC" "v3 eco7, rescue, rho_n, sub-grid 2 + CRC" "v3 eco7, rescue, rho_n, in-cell retry + CRC" "Pilots N3x8 + v3 eco7, rescue, rho_n, fast R=1/10 from -2 dB + CRC" "Pilots N3x8 + v3 eco7, rescue, rho_n, fast R=1/10 from -2 dB, sub-grid 2 + CRC" "Pilots N3x8 + v3 eco7, rescue, rho_n, fast R=1/10 from -2 dB, in-cell retry + CRC" --seed 5701 --part sg-smoke2 > logs/run_sg-smoke2.out 2>&1
