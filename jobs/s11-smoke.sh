#!/bin/bash
# s11-smoke: adopted testing receiver testing vs testing_spec11 over SNR (expected_s11.md, 2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u BLIND_IMPLEMENTATION/testing/run.py --max-frames 400 --points 0.15:-4.5:4 0.15:1:4 --seed 7930 --rx testing testing_spec11 --part t-s11-smoke
  echo "ALL DONE" ) > logs/run_s11-smoke.out 2>&1
