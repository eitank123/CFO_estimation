#!/bin/bash
# nnb2: retry gate (nn_b) online, paired vs the q_fix baseline, 64k per point (2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
( $PY -u BLIND_IMPLEMENTATION/testing/run.py --max-frames 4000 --points 1/2:2:16 --rx base2_qfix base2_qfix_nnb1 --seed 7744 --part t-nnb2
  echo "ALL DONE" ) > logs/run_nnb2.out 2>&1
