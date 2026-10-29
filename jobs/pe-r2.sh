#!/bin/bash
# pe-r2: pilots + v3 eco+ (eco, code-aided retry, posterior final 8), paired with ec-r2a (same seed)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/2:2:8 1/2:2.5:8 1/2:3:8 1/2:3.5:8 1/2:4:8 1/2:5:8  --max-frames 50000 --min-errors 100 --rx "Pilots N3x8 + v3 eco+ + CRC" "Pilots N4x4 + v3 eco+ + CRC" "Pilots C16 + v3 eco+ + CRC" --seed 5703 --part pe-r2 > logs/run_pe-r2.out 2>&1
