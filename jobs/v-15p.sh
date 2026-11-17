#!/bin/bash
# v-15p: R = 0.15, pn 0, 480k per SNR, -4.5 -4 -3.5 dB (high SNRs: v-15p2), --min-err 200 as e5-pp (stops where every source fails): ViaSat 7653150, ViaSat top32 X4phase, hyb3-pre48, hyb3-pre48 wide + parents
# (faithful variants of the est5 competitors, expected_variants.md, 2026-11-15; each variant McNemar-paired with its parent)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs est4/logs est4/results
( $PY -u est4/run_bler.py --rate 0.15 --snrs -4.5 -4 -3.5 --frames 480000 --min-err 200 --chunks 120 --seed 103 --pn 0 --sources "ViaSat UW" "ViaSat 7653150" "ViaSat top32 X4phase" "hyb3" "hyb3-pre48" "hyb3-pre48 wide" --part v-15p
  echo "ALL DONE" ) > logs/run_v-15p.out 2>&1
