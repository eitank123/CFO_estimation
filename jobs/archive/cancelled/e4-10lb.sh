#!/bin/bash
# e4-10lb: est4 R = 1/10 low-SNR extension (per-symbol -6.0 dB), pn 0, 480k (presentation waterfall, 2026-11-16)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs est4/logs est4/results
( $PY -u est4/run_bler.py --rate 1/10 --snrs -6.0 --frames 480000 --min-err 100000 --chunks 120 --seed 57 --pn 0 --sources Genie "RCS2-13" "pre128 M&M" "pre128 ML" "split64 ML" --part e4-10lb
  echo "ALL DONE" ) > logs/run_e4-10lb.out 2>&1
