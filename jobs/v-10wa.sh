#!/bin/bash
# v-10wa: R = 1/10, pn 0, 480k per SNR in chunks of 4000, SNRs -5 -4.5 (re-split of v-10w after v-smoke, 2026-11-15): WiFi real320, WiFi real320 lobes + parent WiFi pre128
# (faithful variants of the est5 competitors, expected_variants.md, 2026-11-15; each variant McNemar-paired with its parent)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs est4/logs est4/results
( $PY -u est4/run_bler.py --rate 1/10 --snrs -5 -4.5 --frames 480000 --min-err 100000 --chunks 120 --seed 147 --pn 0 --sources "WiFi pre128" "WiFi real320" "WiFi real320 lobes" --part v-10wa
  echo "ALL DONE" ) > logs/run_v-10wa.out 2>&1
