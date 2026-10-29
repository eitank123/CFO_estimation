#!/bin/bash
# cl-train: cell-grader NN for the R = 1/10 search (blind_cell_nn.py): dump the cells of eco7 (blind, 24 pilots), train
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/models blind/results
$PY -u blind_cell_nn.py data --mode blind --rate 1/10 --workers 8 --frames 400 > logs/run_cl-data-blind.out 2>&1 &
$PY -u blind_cell_nn.py data --mode pilots --rate 1/10 --workers 8 --frames 600 > logs/run_cl-data-pilots.out 2>&1 &
wait
$PY -u blind_cell_nn.py train --mode blind --rate 1/10 > logs/run_cl-train-blind.out 2>&1 &
$PY -u blind_cell_nn.py train --mode pilots --rate 1/10 > logs/run_cl-train-pilots.out 2>&1 &
wait
echo "CL DONE" > logs/run_cl-train.out
