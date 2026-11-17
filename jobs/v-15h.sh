#!/bin/bash
# v-15h: R = 0.15, pn 0, 480k per SNR, low half of the e5-15 grid (high: v-15h2): DVB-S2 header90 + parent DVB-S2 style
# (faithful variants of the est5 competitors, expected_variants.md, 2026-11-15; each variant McNemar-paired with its parent;
# header90 / SOF26 scan k STEP over the whole +-0.03, ~801 hypotheses per packet at every SNR)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs est4/logs est4/results
( $PY -u est4/run_bler.py --rate 0.15 --snrs -4.5 -4 -3.5 --frames 480000 --min-err 100000 --chunks 120 --seed 102 --pn 0 --sources "DVB-S2 style" "DVB-S2 header90" --part v-15h
  echo "ALL DONE" ) > logs/run_v-15h.out 2>&1
