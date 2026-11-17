#!/bin/bash
# fx-25p1: R = 2/5, pn 0, fixed-search test (expected_fx.md), re-split of fx-25 / fx-2 for the 30-min budget (2026-11-17):
# pre128 ML + VDE-SAT fixed at data Es/N0 0.5, 480k packets, seed 190
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs est4/logs est4/results
( $PY -u est4/run_bler.py --rate 2/5 --snrs 0.5 --frames 480000 --min-err 100000 --chunks 120 --seed 190 --pn 0 --sources "pre128 ML" "VDE-SAT fixed" --part fx-25p1
  echo "ALL DONE" ) > logs/run_fx-25p1.out 2>&1
