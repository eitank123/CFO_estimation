#!/bin/bash
# b15b: final blind receiver at R = 0.15 (R = 1/10 settings, own RHO_N), seed 720b
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
$PY -u blind_ber.py --max-frames 25000 --min-errors 100000 --points 0.15:-3:12 0.15:-2.5:12 0.15:-2:12 --rx "S blind final v2" --seed 7202 --part b15b > logs/run_b15b.out 2>&1
echo "ALL DONE" >> logs/run_b15b.out
