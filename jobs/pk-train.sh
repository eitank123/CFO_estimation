#!/bin/bash
# pk-train: the fast-path peak grader NN (blind_peak_nn.py), blind and 24-pilot models in parallel, then their eval
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/models
$PY -u blind_peak_nn.py train --mode blind --producers 7 > logs/run_pk-train-blind.out 2>&1 &
$PY -u blind_peak_nn.py train --mode pilots --producers 7 > logs/run_pk-train-pilots.out 2>&1 &
wait
$PY -u blind_peak_nn.py eval --mode blind > logs/run_pk-eval-blind.out 2>&1 &
$PY -u blind_peak_nn.py eval --mode pilots > logs/run_pk-eval-pilots.out 2>&1 &
wait
echo "PK DONE" > logs/run_pk-train.out
