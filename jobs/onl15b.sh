#!/bin/bash
# onl15b: online F3 (lmarg 2 / 4) and DD refinement (ddref) vs testing_s11g on the same packets, R = 0.15 -3.5 dB, 16 x 4000 = 64k packets (2026-11-16, expected_online_f3dd.md)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( $R --max-frames 4000 --seed 8033 --points 0.15:-3.5:16 --rx testing_s11g testing_s11g_lm2 testing_s11g_lm4 testing_s11g_ddref --part t-onl15b
  echo "ALL DONE" ) > logs/run_onl15b.out 2>&1
