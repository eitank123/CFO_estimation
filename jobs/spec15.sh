#!/bin/bash
# spec15: speculative decode (win_spec 4) with / without spec_rho 1.1 vs the testing receiver + q_fix, paired (2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u BLIND_IMPLEMENTATION/testing/run.py --max-frames 4000 --points 0.15:-4:16 0.15:-3:16 --rx nofast15_qfix nofast15_qfix_spec nofast15_qfix_spec11 --seed 7755 --part t-spec15
  echo "ALL DONE" ) > logs/run_spec15.out 2>&1
