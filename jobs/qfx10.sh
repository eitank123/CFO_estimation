#!/bin/bash
# qfx10: q_fix paired at the 2-phase points of 1/10 and 0.15 (0.15 -1 dB 128k) (2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py --max-frames 4000"
( $R --points 1/10:-1:16 1/10:0:16 0.15:-1:32 0.15:0:16 0.15:1:16 --rx base10 base10_qfix --seed 7711 --part t-qfx10
  echo "ALL DONE" ) > logs/run_qfx10.out 2>&1
