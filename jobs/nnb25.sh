#!/bin/bash
# nnb25: retry gate (nn_b) online, paired vs the q_fix baseline, 64k per point (2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u BLIND_IMPLEMENTATION/testing/run.py --max-frames 4000 --points 2/5:0.5:16 --rx base25_qfix base25_qfix_nnb1 base25_qfix_nnb01 --seed 7743 --part t-nnb25
  echo "ALL DONE" ) > logs/run_nnb25.out 2>&1
