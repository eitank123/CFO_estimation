#!/bin/bash
# dgb2: decode dumps at more SNRs for the retry gate (1/2) (2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( $R --max-frames 4000 --seed 7793 --points 1/2:1.5:8 1/2:2.5:8 --rx base2_qfix_dump --part t-dgb2
  echo "ALL DONE" ) > logs/run_dgb2.out 2>&1
