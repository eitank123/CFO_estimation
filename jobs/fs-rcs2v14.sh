#!/bin/bash
# fs-rcs2v14: DVB-RCS2 ID 14 (QPSK 1/2, 188 B) ideal-sync PER vs TR T10.6 (1.49 / 1.71 dB), max-log, ADAPTIVE sf (default), 8 it, aff3ct interleaver
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_rcs2.py --wf 14 --snrs 0.89 1.09 1.29 1.49 1.69 1.89 2.09 --frames 1000000 --max-err 300 --seed 14 --workers 16 --part fs-rcs2v14
  $PY -u fullsys/run_rcs2.py --wf 14 --snrs 1.71 --frames 10000000 --max-err 100 --seed 114 --workers 16 --part fs-rcs2v14b
  echo "ALL DONE" ) > logs/run_fs-rcs2v14.out 2>&1
