#!/bin/bash
# fzs-lo: F5 online (fzstop, rate-keyed thresholds) vs the baseline on the same packets below the fitted points: R = 2/5 0 dB (base25_qfix, 16 x 400 = 6400) and 0.15 -5 dB (testing_s11g, 16 x 300 = 4800); ~ the wall time of fzs25a (2026-11-15, expected_f3f5.md F5 online review note)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( $R --max-frames 400 --seed 8071 --points 2/5:0:16 --rx base25_qfix base25_qfix_fzs --part t-fzs-lo-a
  $R --max-frames 300 --seed 8072 --points 0.15:-5:16 --rx testing_s11g testing_s11g_fzs --part t-fzs-lo-b
  echo "ALL DONE" ) > logs/run_fzs-lo.out 2>&1
