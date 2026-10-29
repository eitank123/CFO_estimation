#!/bin/bash
# p64out-a: 64-symbol preamble CFO MSE / outage / wrong lobe of M&M, SNR-aware NN, split ML and split NN (cfo_p64.py)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs lowrate/logs
$PY -u cfo_p64.py --part a --workers 16 > logs/run_p64out-a.out 2>&1
