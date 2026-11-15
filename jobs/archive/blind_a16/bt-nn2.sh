#!/bin/bash
# bt-nn2: blind NN posterior over the 4th-power bins (blind_nn.py), then T1 coarse-estimator test (blind_cfo.py coarse)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/models blind/results
$PY -u blind_nn.py --epochs 60 --steps 300 --batch 256 --producers 13 --threads 3 > logs/run_bt-nn2.out 2>&1
$PY -u blind_cfo.py coarse --frames 20000 --part b > logs/run_bt-coarse2.out 2>&1
