#!/bin/bash
# e5-25: est5 deployed preamble / pilot competitors, R = 2/5, pn 0, 480k packets per SNR in chunks of 4000 (expected_est5.md, 2026-11-15)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs est4/logs est4/results
( $PY -u est4/run_bler.py --rate 2/5 --snrs 0 0.5 1 1.5 2 --frames 480000 --min-err 100000 --chunks 120 --seed 64 --pn 0 --sources Genie "VDE-SAT" "DVB-S2 style" "CCSDS style" "CCSDS style blocks" "DMRS 1/7" "Sparse pilots 1/32" "WiFi pre128" "MIL-110 HF" --part e5-25
  echo "ALL DONE" ) > logs/run_e5-25.out 2>&1
