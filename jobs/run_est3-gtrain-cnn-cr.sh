#!/bin/bash
# est3 CNN training on 1 GPU (CUDA env torch-cuda), on-the-fly full-chain data from 14 CPU workers
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
/gpfs0/bgu-haimp/users/karpei/env/torch-cuda/bin/python -u est3/nn.py train --what cnn-cr --device cuda --epochs 60 --steps 2000 --batch 512 --workers 14 > logs/run_est3-gtrain-cnn-cr.out 2>&1
