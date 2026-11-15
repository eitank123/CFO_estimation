#!/bin/bash
# onl-smoke: online F3 / DD refinement smoke (testing_s11g + _lm2 / _lm4 / _ddref on the same packets), R = 0.15 -4 dB, 4 x 100 packets (2026-11-16, expected_online_f3dd.md)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( $R --max-frames 100 --seed 8031 --points 0.15:-4:4 --rx testing_s11g testing_s11g_lm2 testing_s11g_lm4 testing_s11g_ddref --part t-onl-smoke
  echo "ALL DONE" ) > logs/run_onl-smoke.out 2>&1
