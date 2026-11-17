#!/bin/bash
# onl-smoke: online F3 / DD refinement smoke, 6 arms on the same packets, R = 0.15 -4 and -5 dB, 4 x 100 packets each (2026-11-15, expected_online_f3dd.md)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( $R --max-frames 100 --seed 8031 --points 0.15:-4:4 0.15:-5:4 --rx testing_s11g testing_s11g_lm2 testing_s11g_lm4 testing_s11g_lm2z testing_s11g_ddref testing_s11g_ddref_s2 --part t-onl-smoke 
  echo "ALL DONE" ) > logs/run_onl-smoke.out 2>&1
