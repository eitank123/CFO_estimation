#!/bin/bash
# fzs-r-smoke: F5 early stop smoke at 1/2 and 1/10 (rate-keyed thresholds, first run of these arms), 2 x 100 packets per point (2026-11-15, user request; predictions in BLIND_IMPLEMENTATION/testing/results/expected_f3f5.md "F5 online at 1/10 and 1/2")
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( $R --max-frames 100 --seed 8223 --points 1/2:1.5:2 --rx base2_qfix base2_qfix_fzs --part t-fzs-r-smoke-a
  $R --max-frames 100 --seed 8223 --points 1/10:-5:2 --rx testing_s11g testing_s11g_fzs --part t-fzs-r-smoke-b
  echo "ALL DONE" ) > logs/run_fzs-r-smoke.out 2>&1
