#!/bin/bash
# nph15b: R = 0.15 0 dB, variant nph4 (4 phase hypotheses + sub-offsets at every SNR), paired with b15c (seed 7203)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u testing/run.py --points 0.15:0:16 --rx nph4 --max-frames 25000 --seed 7203 --part nph15b
  echo "ALL DONE" ) > logs/run_nph15b.out 2>&1
