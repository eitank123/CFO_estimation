#!/bin/bash
# pns0: AWGN no-loss check of pns (assumed linewidth 1e-4), 64k paired, base (+ rhos_log) vs pns (2026-11-15, expected_pns.md)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( $R --max-frames 4000 --seed 7966 --points 0.15:-4:16 --rx testing_s11g_rhosl testing_s11g_pns --part t-pns0a
  $R --max-frames 4000 --seed 7966 --points 2/5:0.5:16 --rx base25_qfix_rhosl base25_qfix_pns --part t-pns0b
  echo "ALL DONE" ) > logs/run_pns0.out 2>&1
