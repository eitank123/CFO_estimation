#!/bin/bash
# fx-s15: R = 0.15, pn 0, "VDE-SAT scan" (VDE-SAT layout, full-range CRC scan as the DVB-S2 header; expected_fx.md) + "VDE-SAT fixed" (paired), 480k per SNR, seed 189 (2026-11-17)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs est4/logs est4/results
( $PY -u est4/run_bler.py --rate 0.15 --snrs -4.0 -3.5 -3.0 -2.5 --frames 480000 --min-err 100000 --chunks 120 --seed 189 --pn 0 --sources "VDE-SAT fixed" "VDE-SAT scan" --part fx-s15
  echo "ALL DONE" ) > logs/run_fx-s15.out 2>&1
