#!/bin/bash
# s11-15a: adopted testing receiver testing vs testing_spec11 over SNR (expected_s11.md, 2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u BLIND_IMPLEMENTATION/testing/run.py --max-frames 4000 --points 0.15:-4:16 0.15:-3.5:16 0.15:-3:16 0.15:-2.5:16 --seed 7933 --rx testing testing_spec11 --part t-s11-15a
  echo "ALL DONE" ) > logs/run_s11-15a.out 2>&1
