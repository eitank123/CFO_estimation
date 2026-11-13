#!/bin/bash
# acct-smoke: smoke: accounting fix (old_acct pairs), d4a/d4b counters, accept tags, fe/ud indices
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u BLIND_IMPLEMENTATION/testing/run.py --points 0.15:-4.5:4 --rx base10 base10_oldacct nofast15 nofast15_oldacct nofast_spec_t --max-frames 25 --seed 7898 --part t-acct-smoke-a
  $PY -u BLIND_IMPLEMENTATION/testing/run.py --points 2/5:0:4 --rx base25 base25_oldacct nofast_25 --max-frames 25 --seed 7898 --part t-acct-smoke-b
  echo "ALL DONE" ) > logs/run_acct-smoke.out 2>&1
