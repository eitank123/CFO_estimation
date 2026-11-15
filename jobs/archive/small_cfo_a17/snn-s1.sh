#!/bin/bash
# snn-s1: the 128-pilot split NN retrained for CFO in [-0.03, 0.03] (same architecture as models/cfo_split_nn_L1024.pth:
# conv soft-argmax + 3-lobe classifier, DFT init), study CFO_STUDY=small_cfo (models / logs in small_cfo/)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=small_cfo BLIND_STUDY=small_cfo CFO_MAX=0.03
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/models small_cfo/logs small_cfo/results small_cfo/plots
$PY -u train_cfo_split_nn.py --packet 1024 --init dft --arch conv --lobe 3 --epochs 160 --tag small --producers 15 --threads 1 --workers 16 > logs/run_snn-s1.out 2>&1 \
  && cp small_cfo/models/cfo_split_nn_L1024_small.pth small_cfo/models/cfo_split_nn_L1024.pth && echo "COPIED" >> logs/run_snn-s1.out
