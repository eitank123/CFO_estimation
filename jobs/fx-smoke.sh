#!/bin/bash
# fx-smoke: R = 0.15, pn 0, 8000 packets in 4 chunks, SNR -3.5 (code review 2026-11-17): the fixed CFO searches
# "RCS2-13 wide" (CRC-search window +-3e-3 over the pre/post fringes) and "VDE-SAT fixed" (unclipped alias-period
# window, +-2 alias lobes, alias window x 1.7) next to their parents and pre128 ML (same bursts per layout: McNemar-paired)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs est4/logs est4/results
( $PY -u est4/run_bler.py --rate 0.15 --snrs -3.5 --frames 8000 --min-err 100000 --chunks 4 --seed 181 --pn 0 --sources "pre128 ML" "RCS2-13" "RCS2-13 wide" "VDE-SAT" "VDE-SAT fixed" --part fx-smoke
  echo "ALL DONE" ) > logs/run_fx-smoke.out 2>&1
