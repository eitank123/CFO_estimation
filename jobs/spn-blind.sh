#!/bin/bash
# spn-blind: the SNR-aware cell-prior NN of the small-CFO search (small_prior_nn.py), mode blind: train, then the offline
# evaluation (true-cell rank: periodogram vs NN; NN shortlist size and misses)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results small_cfo/blind/models
: > logs/run_spn-blind.out
$PY -u small_prior_nn.py train --mode blind --epochs 40 --steps 150 --producers 14 --threads 2 >> logs/run_spn-blind.out 2>&1   && $PY -u small_prior_nn.py eval --mode blind --frames 20000 >> logs/run_spn-blind.out 2>&1
