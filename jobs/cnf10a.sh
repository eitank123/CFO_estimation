#!/bin/bash
# cnf10a: 1/10 -5 dB 400k: nofast15 vs nofast_spec_t (chunks 0-15 replay nf10a, seed 7701) (new accounting, 2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py --max-frames 4000"
( $R --points 1/10:-5:100 --rx nofast15 nofast_spec_t --seed 7701 --part t-cnf10a
  echo "ALL DONE" ) > logs/run_cnf10a.out 2>&1
