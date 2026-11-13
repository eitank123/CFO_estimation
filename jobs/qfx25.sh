#!/bin/bash
# qfx25: q_fix paired at 2/5 and 1/2 (2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py --max-frames 4000"
( $R --points 2/5:0.5:16 2/5:1:16 --rx base25 base25_qfix --seed 7712 --part t-qfx25
  $R --points 1/2:2:16 1/2:2.5:16 --rx base2 base2_qfix --seed 7713 --part t-qfx2
  echo "ALL DONE" ) > logs/run_qfx25.out 2>&1
