#!/bin/bash
# fx3-r10b: the rescue receivers at the rest of the R = 1/10 SNRs (complete curves)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/10:-2:8 1/10:-1:8 1/10:0:8 --max-frames 50000 --min-errors 100 --rx "v3 eco7, rescue + CRC" --seed 5701 --part fx3-r10b > logs/run_fx3-r10b.out 2>&1
