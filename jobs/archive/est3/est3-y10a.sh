#!/bin/bash
# est3-y10a: more packets for bler_more R = 1/10: joint ML + CNN, seed 1 (seed 0 = kb10 / kn10)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs est3/logs est3/results
( $PY -u est3/run_bler.py --rate 1/10 --snrs -5 -4.5 -4 -3 -2 -1 0 --sources 'Joint ML Lh=3' cnn-cr --max-frames 960000 --min-errors 2000 --seed 1 --part y10a
  echo "ALL DONE" ) > logs/run_est3-y10a.out 2>&1
