#!/bin/bash
# blb-g: blind NN-ranked-peak receiver BLER (needs blind/models/blind_nn.pth)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results
$PY -u blind_ber.py --points 1/4:0:2 1/4:1:2 1/4:2:4 1/4:3:4 1/4:4:4 1/4:5:4 1/2:2:2 1/2:3:4 1/2:4:4 1/2:5:4 1/2:6:4 --max-frames 30000 --min-errors 100 --rx "NN peaks + SC search + CRC" --seed 4040 --part g > logs/run_blb-g.out 2>&1
