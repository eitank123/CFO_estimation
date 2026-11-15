#!/bin/bash
# rn-r25: the search order re-scored by the cell-ranking NN (top 512 cells), blind R = 2/5 (paired with eco6/eco7)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 2/5:0.5:8 2/5:1:8 2/5:1.5:8 2/5:2:8 --max-frames 50000 --min-errors 100 --rx "v3 eco7, rank NN + CRC" --seed 5702 --part rn-r25 > logs/run_rn-r25.out 2>&1
