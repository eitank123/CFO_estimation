#!/bin/bash
# bf-b: blind best-first search (blind_fast.py), BLER + wall time, points 1/10:-2:8 1/10:-1.5:8 1/10:-1:8 1/10:-0.5:8 1/10:0:8
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results
$PY -u blind_ber.py --points 1/10:-2:8 1/10:-1.5:8 1/10:-1:8 1/10:-0.5:8 1/10:0:8 --max-frames 50000 --min-errors 100 --rx "Best-first search (spectral + 4th) + CRC" --seed 5102 --part bf-b > logs/run_bf-b.out 2>&1
