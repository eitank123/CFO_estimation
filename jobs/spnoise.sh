#!/bin/bash
# spnoise: spec11 final checks (expected_spec1m.md, 2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u BLIND_IMPLEMENTATION/testing/run.py --noise-only --max-frames 100 --min-errors 100000 --points 1/10:-5:16 0.15:-4:16 --rx nofast15_qfix nofast15_qfix_spec11 --seed 7871 --part t-spnoise
  echo "ALL DONE" ) > logs/run_spnoise.out 2>&1
