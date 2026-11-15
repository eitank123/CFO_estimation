#!/bin/bash
# pn1: Wiener phase noise linewidth x Ts = 1e-5, testing receivers + genie (2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( BLIND_PN=1e-5 $R --max-frames 4000 --seed 7771 --points 0.15:-3.5:16 1/10:-5:16 --rx nofast15_qfix --part t-pn1a
  BLIND_PN=1e-5 $R --max-frames 4000 --seed 7781 --points 2/5:0.5:16 --rx base25_qfix --part t-pn1b
  echo "ALL DONE" ) > logs/run_pn1.out 2>&1
