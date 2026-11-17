#!/bin/bash
# fzs-smoke: F5 online smoke (fzstop; baseline + _fzs on the same packets), R = 2/5 0.5 dB and 0.15 -4 dB, 4 x 100 packets each (2026-11-15, expected_f3f5.md F5 online)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( $R --max-frames 100 --seed 8041 --points 2/5:0.5:4 --rx base25_qfix base25_qfix_fzs --part t-fzs-smoke-a
  $R --max-frames 100 --seed 8041 --points 0.15:-4:4 --rx testing_s11g testing_s11g_fzs --part t-fzs-smoke-b
  echo "ALL DONE" ) > logs/run_fzs-smoke.out 2>&1
