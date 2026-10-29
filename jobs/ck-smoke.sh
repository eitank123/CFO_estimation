#!/bin/bash
# ck-smoke: tiny train + eval of the checkpoint NN (small_ck_nn.py), both modes, to check the code runs
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results small_cfo/blind/models
: > logs/run_ck-smoke.out
for m in blind pilots; do
  $PY -u small_ck_nn.py train --mode $m --epochs 2 --steps 4 --val 40 --producers 8 >> logs/run_ck-smoke.out 2>&1
  $PY -u small_ck_nn.py eval --mode $m --frames 40 >> logs/run_ck-smoke.out 2>&1
done
