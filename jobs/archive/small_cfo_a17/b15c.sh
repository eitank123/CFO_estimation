#!/bin/bash
# b15c: final blind receiver at R = 0.15 (R = 1/10 settings, own RHO_N), seed 720c
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
$PY -u blind_ber.py --max-frames 25000 --min-errors 100000 --points 0.15:-1:16 0.15:0:16 0.15:1:16 --rx "S blind final v2" --seed 7203 --part b15c > logs/run_b15c.out 2>&1
echo "ALL DONE" >> logs/run_b15c.out
