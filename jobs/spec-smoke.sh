#!/bin/bash
# spec-smoke: smoke of the speculative decode with the stricter acceptance (spec_rho) (2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u BLIND_IMPLEMENTATION/testing/run.py --max-frames 25 --seed 7899 --points 1/10:-5.5:4 0.15:-4.5:4 --rx nofast15_qfix nofast15_qfix_spec nofast15_qfix_spec11 --part t-spec-smoke
  echo "ALL DONE" ) > logs/run_spec-smoke.out 2>&1
