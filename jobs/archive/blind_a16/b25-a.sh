#!/bin/bash
# b25-a: blind / few-pilot BLER at R=2/5 (819 data bits), points 2/5:0.5:8 2/5:1:8 2/5:1.5:8 2/5:2:8
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 2/5:0.5:8 2/5:1:8 2/5:1.5:8 2/5:2:8 --max-frames 50000 --min-errors 100 --rx "Best-first search v3 + CRC" "Best-first search v2 + CRC" "Genie (known CFO, pre-MF correction)" --seed 5501 --part b25-a > logs/run_b25-a.out 2>&1
