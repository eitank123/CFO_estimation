#!/bin/bash
# pns1c: pn 1e-4, R = 2/5 0.5 dB, 64k, pns arm; paired with pns1b (same seed) (2026-11-15, expected_pns.md)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( BLIND_PN=1e-4 $R --max-frames 4000 --seed 7961 --points 2/5:0.5:16 --rx base25_qfix_pns --part t-pns1c
  echo "ALL DONE" ) > logs/run_pns1c.out 2>&1
