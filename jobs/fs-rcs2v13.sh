#!/bin/bash
# fs-rcs2v13: DVB-RCS2 ID 13 (QPSK 1/3, 123 B) ideal-sync PER vs TR T10.6 (-0.80 / -0.51 dB), max-log, ADAPTIVE sf (default), 8 it, aff3ct interleaver
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_rcs2.py --wf 13 --snrs -1.40 -1.20 -1.00 -0.80 -0.60 -0.40 -0.20 --frames 1000000 --max-err 300 --seed 13 --workers 16 --part fs-rcs2v13
  $PY -u fullsys/run_rcs2.py --wf 13 --snrs -0.51 --frames 10000000 --max-err 100 --seed 113 --workers 16 --part fs-rcs2v13b
  echo "ALL DONE" ) > logs/run_fs-rcs2v13.out 2>&1
