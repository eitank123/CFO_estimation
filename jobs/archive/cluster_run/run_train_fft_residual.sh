#!/bin/bash
# Submit from bhn20:
#   runai-bgu submit python -n cfo-fft-residual -c 8 -m 8Gi -- "bash /gpfs0/bgu-haimp/users/karpei/CFO_estimation/run_train_fft_residual.sh"
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 MPLBACKEND=Agg
/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python -u train_fft_nn.py --mode residual --epochs 150 --steps 500 --threads 8 > train_fft_nn_residual.log 2>&1
