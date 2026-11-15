#!/bin/bash
# ev-r2: v3 eco+ with the extra decodes verified, paired with ec-r2a / ep-r2 (same seed)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/2:2:8 1/2:2.5:8 1/2:3:8 1/2:3.5:8 1/2:4:8 1/2:5:8  --max-frames 50000 --min-errors 100 --rx "v3 eco+ verified + CRC" "v3 eco+ verified, all search passes + CRC" --seed 5703 --part ev-r2 > logs/run_ev-r2.out 2>&1
