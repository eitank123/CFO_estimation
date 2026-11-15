#!/bin/bash
# p64-snn: split-pilot NN on 2 x 32 pilots (quarter layout, 1024 symbols), the convlobe-long design, then its 1e6-frame evaluation
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate CFO_BLOCK=32
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs lowrate/logs lowrate/models
$PY -u train_cfo_split_nn.py --packet 1024 --init dft --arch conv --lobe 3 --epochs 160 --tag B32-convlobe-long --producers 15 --threads 1 --workers 16 > logs/run_p64-snn.out 2>&1
cp lowrate/models/cfo_split_nn_L1024_B32-convlobe-long.pth lowrate/models/cfo_split_nn_L1024_B32.pth && echo "COPIED" >> logs/run_p64-snn.out
