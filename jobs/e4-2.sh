#!/bin/bash
# e4-2: est4 fair pilot competitors, all sources, R = 1/2, pn 0, 480k packets per SNR in chunks of 4000 (expected_est4.md, 2026-11-15)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs est4/logs est4/results
( $PY -u est4/run_bler.py --rate 1/2 --snrs 1.5 2 2.5 3 --frames 480000 --min-err 100000 --chunks 120 --seed 54 --pn 0 --sources Genie "RCS2-13" "RCS2-13 track" "pre128 M&M" "pre128 ML" "split64 ML" "split64 ML interp" --part e4-2
  echo "ALL DONE" ) > logs/run_e4-2.out 2>&1
