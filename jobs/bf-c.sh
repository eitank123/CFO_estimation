#!/bin/bash
# bf-c: blind best-first search (blind_fast.py), BLER + wall time, points 1/4:0:8 1/4:0.5:8 1/4:1:8 1/4:1.5:8 1/4:2:8 1/4:2.5:4 1/4:3:4 1/4:4:4 1/2:2:4 1/2:2.5:4 1/2:3:4 1/2:3.5:4 1/2:4:4 1/2:5:4
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results
$PY -u blind_ber.py --points 1/4:0:8 1/4:0.5:8 1/4:1:8 1/4:1.5:8 1/4:2:8 1/4:2.5:4 1/4:3:4 1/4:4:4 1/2:2:4 1/2:2.5:4 1/2:3:4 1/2:3.5:4 1/2:4:4 1/2:5:4 --max-frames 50000 --min-errors 100 --rx "Best-first search (spectral + 4th) + CRC" --seed 5103 --part bf-c > logs/run_bf-c.out 2>&1
