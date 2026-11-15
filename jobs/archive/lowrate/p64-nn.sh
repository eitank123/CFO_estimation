#!/bin/bash
# p64-nn: SNR-aware NN on a 64-symbol preamble (32 lags), full chain, from scratch -> lowrate/models/snr_aware_cfo_model_L32_chain.pth
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs lowrate/logs
$PY -u train_snr_nn.py --length 64 --no-expert-init --epochs 190 --threads 2 --producers 14 --tag _chain > logs/run_p64-nn.out 2>&1
