#!/bin/bash
# fs-rcs2a3008: AFF3CT Turbo_DB_N3008_K1504 (rate 1/2 = ID 14 code, no UW) exact config via --fmt; AFF3CT Eb/N0 0.0-1.8 (file points, FER down to ~1e-5)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_rcs2.py --fmt aff3ct-N3008 --ebn0-aff3ct 0.0 0.2 0.4 0.6 0.8 1.0 1.2 1.4 1.6 --frames 1000000 --max-err 200 --seed 31 --workers 16 --part fs-rcs2a3008
  $PY -u fullsys/run_rcs2.py --fmt aff3ct-N3008 --ebn0-aff3ct 1.8 --frames 3000000 --max-err 100 --seed 131 --workers 16 --part fs-rcs2a3008b
  echo "ALL DONE" ) > logs/run_fs-rcs2a3008.out 2>&1
