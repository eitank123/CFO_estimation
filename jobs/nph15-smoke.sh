#!/bin/bash
# nph15-smoke: smoke test of testing/run.py variant nph4 (4 phase hypotheses at every SNR), R = 0.15
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u testing/run.py --points 0.15:-1:2 --rx base10 nph4 --max-frames 300 --workers 4 --seed 8998 --part nph15-smoke
  echo "ALL DONE" ) > logs/run_nph15-smoke.out 2>&1
