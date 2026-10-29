#!/bin/bash
# rk-train: the search cell-ranking NN (blind_rank_nn.py), blind and 24 pilots in parallel, then their eval;
# + the fast-path retry statistics of the peak NN (blind_peak_nn.py retry)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/models blind/results
$PY -u blind_rank_nn.py train --mode blind --producers 7 > logs/run_rk-train-blind.out 2>&1 &
$PY -u blind_rank_nn.py train --mode pilots --producers 7 > logs/run_rk-train-pilots.out 2>&1 &
wait
$PY -u blind_rank_nn.py eval --mode blind > logs/run_rk-eval-blind.out 2>&1 &
$PY -u blind_rank_nn.py eval --mode pilots > logs/run_rk-eval-pilots.out 2>&1 &
$PY -u blind_peak_nn.py retry --mode pilots > logs/run_rk-retry-pilots.out 2>&1 &
$PY -u blind_peak_nn.py retry --mode blind > logs/run_rk-retry-blind.out 2>&1 &
wait
echo "RK DONE" > logs/run_rk-train.out
