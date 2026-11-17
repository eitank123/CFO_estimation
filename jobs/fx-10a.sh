#!/bin/bash
# fx-10a: R = 1/10, pn 0, 480k per SNR in chunks of 4000, SNRs -5.4 -5.0 (code review 2026-11-17): the fixed CFO searches
# "RCS2-13 wide" (window +-3e-3 over the pre/post fringes) and "VDE-SAT fixed" (unclipped alias window, +-2 alias lobes,
# alias window x 1.7) + pre128 ML (other seeds than e4: pools with its e4 rows)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs est4/logs est4/results
( $PY -u est4/run_bler.py --rate 1/10 --snrs -5.4 -5.2 --frames 480000 --min-err 100000 --chunks 120 --seed 182 --pn 0 --sources "pre128 ML" "RCS2-13 wide" "VDE-SAT fixed" --part fx-10a
  echo "ALL DONE" ) > logs/run_fx-10a.out 2>&1
