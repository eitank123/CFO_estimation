#!/bin/bash
# fx-r10b5: last-stage rescue of the packets the search loses (final 32 / + top posterior cells + fine refinement)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/10:-5:8 --max-frames 25000 --min-errors 100 --rx "v3 eco7, final 32 + CRC" "v3 eco7, rescue + CRC" --seed 5701 --part fx-r10b5 > logs/run_fx-r10b5.out 2>&1
