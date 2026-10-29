#!/bin/bash
# ck-pilots: the checkpoint NN of the small-CFO search (small_ck_nn.py), mode pilots: one model per checkpoint (1/8 .. 1/2)
# on the partial path metrics of every cell, then the offline evaluation (z-test vs NN: true-cell rank, shortlists)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results small_cfo/blind/models
: > logs/run_ck-pilots.out
$PY -u small_ck_nn.py train --mode pilots >> logs/run_ck-pilots.out 2>&1 && $PY -u small_ck_nn.py eval --mode pilots >> logs/run_ck-pilots.out 2>&1
