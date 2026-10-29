#!/bin/bash
# b25-h: blind / few-pilot BLER at R=2/5 (819 data bits), points 2/5:0.5:2 2/5:1:2 2/5:1.5:2 2/5:2:2 2/5:2.5:2 2/5:3:2
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 2/5:0.5:2 2/5:1:2 2/5:1.5:2 2/5:2:2 2/5:2.5:2 2/5:3:2 --max-frames 10000 --min-errors 100 --rx "4th power + SC search + CRC" "Spectral grid 6 sigma + SC search + CRC" "Best-first search (spectral + 4th) + CRC" --seed 5508 --part b25-h > logs/run_b25-h.out 2>&1
