#!/bin/bash
# est3-crbhi: BLER of the CRB-limited 128-pilot receiver (f + N(0, CRB)) at R = 2/5 and 1/2, seed 1 (paired with m25 / m2)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs est3/logs est3/results
( $PY -u est3/run_bler.py --rate 2/5 --snrs 0 0.5 1 1.5 2 2.5 3 --sources 'CRB 128 pilots' --max-frames 480000 --min-errors 2000 --seed 1 --part crb25
  $PY -u est3/run_bler.py --rate 1/2 --snrs 1.5 2 2.5 3 3.5 4 5 --sources 'CRB 128 pilots' --max-frames 480000 --min-errors 2000 --seed 1 --part crb2
  echo "ALL DONE" ) > logs/run_est3-crbhi.out 2>&1
