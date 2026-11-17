#!/bin/bash
# fzs25a: F5 online (fzstop q 0.7, t 0.774) vs base25_qfix on the same packets, R = 2/5 0.5 dB, 16 x 6250 = 100k (1 of 4 jobs, 400k paired; 2026-11-15, expected_f3f5.md F5 online)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( $R --max-frames 6250 --seed 8042 --points 2/5:0.5:16 --rx base25_qfix base25_qfix_fzs --part t-fzs25a 
  echo "ALL DONE" ) > logs/run_fzs25a.out 2>&1
