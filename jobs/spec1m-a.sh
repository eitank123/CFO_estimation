#!/bin/bash
# spec1m-a: spec11 final checks (expected_spec1m.md, 2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u BLIND_IMPLEMENTATION/testing/run.py --max-frames 4000 --points 1/10:-5:50 --rx nofast15_qfix nofast15_qfix_spec11 --seed 7861 --part t-spec1m-a
  echo "ALL DONE" ) > logs/run_spec1m-a.out 2>&1
