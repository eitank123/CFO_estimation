#!/bin/bash
# bv-c: blind best-first search v3 (blind_fast.py), BLER + wall time, points 1/4:0:8 1/4:0.5:8 1/4:1:8 1/4:1.5:8 1/4:2:8 1/4:2.5:4 1/4:3:4 1/4:4:4
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/4:0:8 1/4:0.5:8 1/4:1:8 1/4:1.5:8 1/4:2:8 1/4:2.5:4 1/4:3:4 1/4:4:4 --max-frames 50000 --min-errors 100 --rx "Best-first search v3 + CRC" "Genie (known CFO, pre-MF correction)" --seed 5303 --part bv-c > logs/run_bv-c.out 2>&1
