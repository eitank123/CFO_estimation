#!/bin/bash
# cap15a: MAC cap 2 M per core vs uncapped, paired, 0.15 -2.5 dB (2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( $R --max-frames 4000 --seed 7761 --points 0.15:-2.5:50 --rx nofast15_qfix nofast15_qfix_cap2 --part t-cap15a
  echo "ALL DONE" ) > logs/run_cap15a.out 2>&1
