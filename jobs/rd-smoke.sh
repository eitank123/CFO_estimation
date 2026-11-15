#!/bin/bash
# rd-smoke: smoke of the Stage 3 refinement diagnostic (small_rx ref_diag, log-only; base + _rd on the same packets), 400 packets per point, all 5 D0 points (2026-11-15, expected_ref.md D0)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( $R --max-frames 100 --seed 8011 --points 1/10:-5:4 0.15:-4:4 0.15:-3:4 --rx testing_s11g testing_s11g_rd --part t-rd-smoke-a
  $R --max-frames 100 --seed 8011 --points 2/5:0.5:4 --rx base25_qfix base25_qfix_rd --part t-rd-smoke-b
  $R --max-frames 100 --seed 8011 --points 1/2:2:4 --rx base2_qfix base2_qfix_rd --part t-rd-smoke-c
  echo "ALL DONE" ) > logs/run_rd-smoke.out 2>&1
