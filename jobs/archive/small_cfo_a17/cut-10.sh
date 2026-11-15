#!/bin/bash
# cut-10: cut-size NN (small_cut_nn.py), R = 1/10: per packet, how many cells to keep at the checkpoint so the true
# cell survives (pinball loss at the 0.999 / 0.9999 quantile), vs the z-test and the checkpoint NN's fixed shortlist
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_cut-10.out
$PY -u small_cut_nn.py --rate 1/10 --train 2000 --test 1000 --workers 16 --seed 7 >> logs/run_cut-10.out 2>&1 && $PY -u small_cut_nn.py --rate 1/10 --train 150000 --test 100000 --workers 16 >> logs/run_cut-10.out 2>&1
