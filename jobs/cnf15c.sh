#!/bin/bash
# cnf15c: 0.15 -1 / 0 dB 400k nofast15; +1 dB 64k nofast15 vs nofast_nph4 (fast path on vs off) (new accounting, 2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py --max-frames 4000"
( $R --points 0.15:-1:100 0.15:0:100 --rx nofast15 --seed 7702 --part t-cnf15c
  $R --points 0.15:1:16 --rx nofast15 nofast_nph4 --seed 7702 --part t-cnf15e
  echo "ALL DONE" ) > logs/run_cnf15c.out 2>&1
