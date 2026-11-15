#!/bin/bash
# bv-g: blind BLER at R=1/3 (replaces R=1/4), points 1/3:0.5:8 1/3:1:8 1/3:1.5:8 1/3:2:8
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/3:0.5:8 1/3:1:8 1/3:1.5:8 1/3:2:8 --max-frames 50000 --min-errors 100 --rx "Best-first search v3 + CRC" "Best-first search v2 + CRC" "Genie (known CFO, pre-MF correction)" --seed 5471 --part bv-g > logs/run_bv-g.out 2>&1
