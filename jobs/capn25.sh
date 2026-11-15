#!/bin/bash
# capn25: noise-only frames through the capped receivers (false alarms, capped cost) (2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( $R --max-frames 625 --noise-only --seed 7766 --points 2/5:1.5:16 --rx base25_qfix_cap1 --part t-capn25
  echo "ALL DONE" ) > logs/run_capn25.out 2>&1
