#!/bin/bash
# rn-r10a: the search order re-scored by the cell-ranking NN (top 512 cells), blind R = 1/10 (paired with eco7)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/10:-5:8 1/10:-4:8 --max-frames 50000 --min-errors 100 --rx "v3 eco7, rank NN + CRC" --seed 5701 --part rn-r10a > logs/run_rn-r10a.out 2>&1
