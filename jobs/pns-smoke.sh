#!/bin/bash
# pns-smoke: smoke of pns / rhos_log at pn 1e-4, 400 packets per arm (base, base + rhos_log, pns, pns + rhos_log), high-BLER points (2026-11-15, expected_pns.md)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( BLIND_PN=1e-4 $R --max-frames 100 --seed 7969 --points 2/5:0:4 --rx base25_qfix base25_qfix_rhosl base25_qfix_pns base25_qfix_pns_rhosl --part t-pns-smoke-a
  BLIND_PN=1e-4 $R --max-frames 100 --seed 7969 --points 0.15:-4:4 --rx testing_s11g testing_s11g_rhosl testing_s11g_pns testing_s11g_pns_rhosl --part t-pns-smoke-b
  echo "ALL DONE" ) > logs/run_pns-smoke.out 2>&1
