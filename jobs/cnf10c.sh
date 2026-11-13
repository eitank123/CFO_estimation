#!/bin/bash
# cnf10c: 1/10 -3..0 dB 160k nofast15; then base10 64k at every 1/10 point (paired on chunks 0-15) (new accounting, 2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py --max-frames 4000"
( $R --points 1/10:-3:40 1/10:-2:40 1/10:-1:40 1/10:0:40 --rx nofast15 --seed 7701 --part t-cnf10c
  $R --points 1/10:-5:16 1/10:-4.5:16 1/10:-4:16 1/10:-3:16 1/10:-2:16 1/10:-1:16 1/10:0:16 --rx base10 --seed 7701 --part t-cnf10d
  echo "ALL DONE" ) > logs/run_cnf10c.out 2>&1
