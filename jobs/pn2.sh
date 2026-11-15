#!/bin/bash
# pn2: Wiener phase noise linewidth x Ts = 1e-4, testing receivers + genie (2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( BLIND_PN=1e-4 $R --max-frames 4000 --seed 7772 --points 0.15:-3.5:16 1/10:-5:16 --rx nofast15_qfix --part t-pn2a
  BLIND_PN=1e-4 $R --max-frames 4000 --seed 7782 --points 2/5:0.5:16 --rx base25_qfix --part t-pn2b
  echo "ALL DONE" ) > logs/run_pn2.out 2>&1
