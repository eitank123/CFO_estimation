#!/bin/bash
# bf-f: blind best-first search v2 (blind_fast.py), BLER + wall time, points 1/10:-5:8 1/10:-4.5:8 1/10:-4:8 1/10:-3.5:8 1/10:-3:8 1/10:-2.5:8
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/10:-5:8 1/10:-4.5:8 1/10:-4:8 1/10:-3.5:8 1/10:-3:8 1/10:-2.5:8 --max-frames 50000 --min-errors 100 --rx "Best-first search v2 + CRC" --seed 5201 --part bf-f > logs/run_bf-f.out 2>&1
