#!/bin/bash
# fs-rcs2v42: DVB-RCS2 ID 42 (pi/2-BPSK 1/3, 123 B) ideal-sync PER vs TR T10.8 (-3.81 / -3.52 dB), max-log, ADAPTIVE sf (default), 8 it, aff3ct interleaver
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_rcs2.py --wf 42 --snrs -4.41 -4.21 -4.01 -3.81 -3.61 -3.41 -3.21 --frames 1000000 --max-err 300 --seed 42 --workers 16 --part fs-rcs2v42
  $PY -u fullsys/run_rcs2.py --wf 42 --snrs -3.52 --frames 10000000 --max-err 100 --seed 142 --workers 16 --part fs-rcs2v42b
  echo "ALL DONE" ) > logs/run_fs-rcs2v42.out 2>&1
