#!/bin/bash
# smoke-stg: smoke: per-stage acceptance counters (stage_1..5)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u blind_ber.py --max-frames 100 --min-errors 100000 --points 1/10:-3:2 --rx "S blind final v2" --seed 7699 --part smoke-stg
  echo "ALL DONE" ) > logs/run_smoke-stg.out 2>&1
