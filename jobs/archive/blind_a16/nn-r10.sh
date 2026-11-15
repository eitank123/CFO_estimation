#!/bin/bash
# nn-r10: v3 with the NN posterior (no pilots), BLER + MACs + outage
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 1/10:-5:4 1/10:-4:4 1/10:-3:4 1/10:-2:4 1/10:-1:4 1/10:0:4 --max-frames 25000 --min-errors 100 --rx "v3 NN posterior + CRC" "v3 NN posterior, adaptive + abort + CRC" "v3 lite + CRC" --seed 5451 --part nn-r10 > logs/run_nn-r10.out 2>&1
