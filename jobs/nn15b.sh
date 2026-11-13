#!/bin/bash
# nn15b: S3 noise-only R = 0.15 0 dB (10k each) + +1 dB cost (64k paired): base10 vs nph15 (seed 7802)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u BLIND_IMPLEMENTATION/testing/run.py --points 0.15:0:16 --rx base10 nph15 --max-frames 625 --noise-only --seed 7802 --part nn15b
  $PY -u BLIND_IMPLEMENTATION/testing/run.py --points 0.15:1:16 --rx base10 nph15 --max-frames 4000 --seed 7802 --part nn15c
  echo "ALL DONE" ) > logs/run_nn15b.out 2>&1
