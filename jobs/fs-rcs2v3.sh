#!/bin/bash
# fs-rcs2v3: DVB-RCS2 ID 3 (QPSK 1/3, 38 B) ideal-sync PER vs TR 101 545-4 T10.5 (-0.27 / 0.22 dB), max-log, ADAPTIVE sf (default), 8 it, aff3ct interleaver
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_rcs2.py --wf 3 --snrs -0.87 -0.67 -0.47 -0.27 -0.07 0.13 0.33 --frames 1000000 --max-err 300 --seed 3 --workers 16 --part fs-rcs2v3
  $PY -u fullsys/run_rcs2.py --wf 3 --snrs 0.22 --frames 10000000 --max-err 100 --seed 103 --workers 16 --part fs-rcs2v3b
  echo "ALL DONE" ) > logs/run_fs-rcs2v3.out 2>&1
