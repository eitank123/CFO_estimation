#!/bin/bash
# pns3b: pn 3e-4, R = 0.15 -3.5 dB, 64k paired, base (+ rhos_log) vs pns (2026-11-15, expected_pns.md)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( BLIND_PN=3e-4 $R --max-frames 4000 --seed 7963 --points 0.15:-3.5:16 --rx testing_s11g_rhosl testing_s11g_pns --part t-pns3b
  echo "ALL DONE" ) > logs/run_pns3b.out 2>&1
