#!/bin/bash
# pns3f: pn 3e-4, R = 1/2 2 dB, 16k, pns arm; paired with pns3e (same seed) (2026-11-15, expected_pns.md)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( BLIND_PN=3e-4 $R --max-frames 1000 --seed 7965 --points 1/2:2:16 --rx base2_qfix_pns --part t-pns3f
  echo "ALL DONE" ) > logs/run_pns3f.out 2>&1
