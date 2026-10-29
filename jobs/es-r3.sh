#!/bin/bash
# es-r3: CFO MSE / outage of every blind version, R = 1/3
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/3:0.5:2 1/3:1:2 1/3:1.5:2 1/3:2:2 1/3:2.5:2 1/3:3:2 1/3:2:2 --max-frames 5000 --min-errors 1000000000 --rx "4th power + SC search + CRC" "Spectral grid 6 sigma + SC search + CRC" "Best-first search (spectral + 4th) + CRC" "Best-first search v2 + CRC" "Best-first search v3 + CRC" --seed 5465 --part es-r3 > logs/run_es-r3.out 2>&1
