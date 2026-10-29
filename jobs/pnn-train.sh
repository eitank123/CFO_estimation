#!/bin/bash
# pnn-train: NN posterior over CFO cells from the blind statistics (blind_post_nn.py), then E5 ranks
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_post_nn.py train --epochs 40 --steps 300 --producers 14 --threads 2 > logs/run_pnn-train.out 2>&1
$PY -u blind_post_nn.py ranks --frames 1000 --chunks 4 --part a > logs/run_pnn-e5.out 2>&1
