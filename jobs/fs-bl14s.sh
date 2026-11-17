#!/bin/bash
# fs-bl14s: blind (adopted 1/2 receiver base2_qfix_fzs, nopi: 4 pi/2 branches, no PiCode) on RCS2 ID 14 shortened (A 1472, E 3008, N 4096), QPSK; paired with fs-pg14s (seed 14)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_blind_fs.py --fmt id14s --snrs 1.00 1.20 1.40 1.60 1.80 2.00 2.20 2.40 2.60 2.80 3.00 --frames 100000 --max-err 200 --stop-per 2e-4 --seed 14 --workers 16 --part fs-bl14s
  echo "ALL DONE" ) > logs/run_fs-bl14s.out 2>&1
