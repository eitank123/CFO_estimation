#!/bin/bash
# bs-e6b: CFO basin of the code metric at the high rates (grid step for R = 3/5, 2/3, 3/4)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results
$PY -u blind_basin.py --part b --frames 500 --chunks 4 --workers 16 --points 3/5:3.5 3/5:4.5 2/3:4.5 2/3:5.5 3/4:5.5 3/4:6.5 > logs/run_bs-e6b.out 2>&1
