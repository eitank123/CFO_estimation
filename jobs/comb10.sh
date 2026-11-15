#!/bin/bash
# comb10: retry gate + stricter speculative decode vs the testing receiver + q_fix, paired (2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( $R --max-frames 4000 --seed 7795 --points 1/10:-5:16 --rx nofast15_qfix nofast15_qfix_nnb1 nofast15_qfix_nnb1_spec11 --part t-comb10
  echo "ALL DONE" ) > logs/run_comb10.out 2>&1
