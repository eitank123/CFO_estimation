#!/bin/bash
# bv-h: blind BLER at R=1/3 (replaces R=1/4), points 1/3:2.5:8 1/3:3:8 1/3:4:8
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/3:2.5:8 1/3:3:8 1/3:4:8 --max-frames 50000 --min-errors 100 --rx "Best-first search v3 + CRC" "Best-first search v2 + CRC" "Genie (known CFO, pre-MF correction)" --seed 5472 --part bv-h > logs/run_bv-h.out 2>&1
