#!/bin/bash
# fs-rcs2a4512: AFF3CT Turbo_DB_N4512_K1504 (rate 1/3, no UW) exact config via --fmt; AFF3CT Eb/N0 0.0-1.0 (file points, FER down to 2.4e-4)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_rcs2.py --fmt aff3ct-N4512 --ebn0-aff3ct 0.0 0.2 0.4 0.6 0.8 1.0 --frames 1000000 --max-err 200 --seed 32 --workers 16 --part fs-rcs2a4512
  echo "ALL DONE" ) > logs/run_fs-rcs2a4512.out 2>&1
