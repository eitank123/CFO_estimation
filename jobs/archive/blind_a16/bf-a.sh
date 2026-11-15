#!/bin/bash
# bf-a: blind best-first search (blind_fast.py), BLER + wall time, points 1/10:-5:8 1/10:-4.5:8 1/10:-4:8 1/10:-3.5:8 1/10:-3:8 1/10:-2.5:8
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results
$PY -u blind_ber.py --points 1/10:-5:8 1/10:-4.5:8 1/10:-4:8 1/10:-3.5:8 1/10:-3:8 1/10:-2.5:8 --max-frames 50000 --min-errors 100 --rx "Best-first search (spectral + 4th) + CRC" --seed 5101 --part bf-a > logs/run_bf-a.out 2>&1
