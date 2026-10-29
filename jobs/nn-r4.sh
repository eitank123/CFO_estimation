#!/bin/bash
# nn-r4: v3 with the NN posterior, R = 1/4 and 1/2
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/4:0:4 1/4:0.5:4 1/4:1:4 1/4:1.5:4 1/4:2:4 1/4:3:4 1/2:2:4 1/2:2.5:4 1/2:3:4 1/2:3.5:4 1/2:4:4 --max-frames 25000 --min-errors 100 --rx "v3 NN posterior + CRC" "v3 NN posterior, adaptive + abort + CRC" "v3 lite + CRC" --seed 5452 --part nn-r4 > logs/run_nn-r4.out 2>&1
