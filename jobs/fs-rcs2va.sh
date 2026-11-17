#!/bin/bash
# fs-rcs2va: AFF3CT Turbo_DB_N2256_K1504 (rate 2/3, no UW) exact config via --fmt; AFF3CT Eb/N0 2.0-2.6 (FER 1.4e-1 ... 4.9e-5)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_rcs2.py --fmt aff3ct-N2256 --ebn0-aff3ct 2.0 2.2 2.4 2.6 --frames 1000000 --max-err 200 --seed 33 --workers 16 --part fs-rcs2va
  echo "ALL DONE" ) > logs/run_fs-rcs2va.out 2>&1
