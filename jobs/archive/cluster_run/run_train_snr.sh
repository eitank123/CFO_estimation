#!/bin/bash
# Submit from bhn20:
#   runai-bgu submit python -n cfo-snr-nn -c 8 -m 8Gi -- "bash /gpfs0/bgu-haimp/users/karpei/CFO_estimation/run_train_snr.sh"
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 MPLBACKEND=Agg
/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python -u train_snr_nn.py --epochs 150 --steps 500 --threads 8 > train_snr_nn.log 2>&1
