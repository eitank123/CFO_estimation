#!/bin/bash
# e4-smoke: est4 fair pilot competitors (pilots outside the packet, DVB-RCS2 layouts), all sources, R = 0.15 -4 dB, pn 0 and 1e-4, 800 packets each (expected_est4.md, 2026-11-15)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs est4/logs est4/results
( $PY -u est4/run_bler.py --rate 0.15 --snrs -4 --frames 800 --min-err 100000 --chunks 2 --seed 50 --pn 0 --part e4-smoke-a
  $PY -u est4/run_bler.py --rate 0.15 --snrs -4 --frames 800 --min-err 100000 --chunks 2 --seed 50 --pn 1e-4 --part e4-smoke-b
  echo "ALL DONE" ) > logs/run_e4-smoke.out 2>&1
