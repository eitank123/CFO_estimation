#!/bin/bash
# es-r10: CFO MSE / outage of every blind version (fixed 10k frames per point)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/10:-5:2 1/10:-4:2 1/10:-3:2 1/10:-2:2 1/10:-1:2 1/10:0:2 --max-frames 5000 --min-errors 1000000000 --rx "4th power + SC search + CRC" "Spectral grid 6 sigma + SC search + CRC" "Best-first search (spectral + 4th) + CRC" "Best-first search v2 + CRC" "Best-first search v3 + CRC" --seed 5441 --part es-r10 > logs/run_es-r10.out 2>&1
