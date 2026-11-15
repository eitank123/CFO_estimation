#!/bin/bash
# t-smoke: testing/ Stage 3 dump smoke test (R = 1/10 -5 dB, R = 0.15 -3 dB, 1 chunk of 300 packets each)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results testing/results
( $PY -u testing/run.py --points 1/10:-5:2 0.15:-3:2 --rx base10 --dump --max-frames 300 --workers 4 --seed 8999 --part t-smoke
  ls testing/results/dumps/t-smoke | head; ls testing/results/dumps/t-smoke | wc -l
  echo "ALL DONE" ) > logs/run_t-smoke.out 2>&1
