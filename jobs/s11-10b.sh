#!/bin/bash
# s11-10b: adopted testing receiver testing vs testing_spec11 over SNR (expected_s11.md, 2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u BLIND_IMPLEMENTATION/testing/run.py --max-frames 4000 --points 1/10:-3:16 1/10:-2:16 1/10:-1:16 1/10:0:16 --seed 7932 --rx testing testing_spec11 --part t-s11-10b
  echo "ALL DONE" ) > logs/run_s11-10b.out 2>&1
