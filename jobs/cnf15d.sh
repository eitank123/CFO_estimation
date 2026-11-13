#!/bin/bash
# cnf15d: 0.15 base10 64k at every point + nofast15 at -4 dB; 2/5 and 1/2 nofast scan 32k (new accounting, 2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py --max-frames 4000"
( $R --points 0.15:-4:16 --rx base10 nofast15 --seed 7702 --part t-cnf15d
  $R --points 0.15:-3.5:16 0.15:-3:16 0.15:-2.5:16 0.15:-2:16 0.15:-1:16 0.15:0:16 0.15:1:16 --rx base10 --seed 7702 --part t-cnf15f
  $R --points 2/5:0.5:8 2/5:1:8 --rx base25 nofast_25 --seed 7703 --part t-cnf25
  $R --points 1/2:2:8 1/2:2.5:8 --rx base2 nofast_2 --seed 7704 --part t-cnf2
  echo "ALL DONE" ) > logs/run_cnf15d.out 2>&1
