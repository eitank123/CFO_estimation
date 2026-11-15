#!/bin/bash
# bv-i: blind BLER at R=1/3 (replaces R=1/4), points 1/3:0.5:2 1/3:1:2 1/3:1.5:2 1/3:2:2 1/3:2.5:2 1/3:3:2
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/3:0.5:2 1/3:1:2 1/3:1.5:2 1/3:2:2 1/3:2.5:2 1/3:3:2 --max-frames 10000 --min-errors 100 --rx "4th power + SC search + CRC" "Spectral grid 6 sigma + SC search + CRC" "Best-first search (spectral + 4th) + CRC" --seed 5473 --part bv-i > logs/run_bv-i.out 2>&1
