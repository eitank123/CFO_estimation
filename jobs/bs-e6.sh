#!/bin/bash
# bs-e6: CFO basin of the code metric with per-segment phase tracking / 4th-power snapping (blind_basin.py)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results
$PY -u blind_basin.py --part a --frames 500 --chunks 4 --workers 16 > logs/run_bs-e6.out 2>&1
