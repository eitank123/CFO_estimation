#!/bin/bash
# nn15a: S3 noise-only false alarms R = 0.15 -1 dB: base10 vs nph15, 10k each (seed 7801)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u BLIND_IMPLEMENTATION/testing/run.py --points 0.15:-1:16 --rx base10 nph15 --max-frames 625 --noise-only --seed 7801 --part nn15a
  echo "ALL DONE" ) > logs/run_nn15a.out 2>&1
