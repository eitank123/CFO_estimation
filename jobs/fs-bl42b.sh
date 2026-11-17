#!/bin/bash
# fs-bl42b: blind (base25_qfix_fzs, bpsk_sq: line / phases from r^2) on RCS2 ID 42 pi/2-BPSK (A 952, E 2952 symbols, N 4096 puncture); paired with fs-pg42b (seed 42)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_blind_fs.py --fmt id42b --snrs -4.40 -4.20 -4.00 -3.80 -3.60 -3.40 -3.20 -3.00 -2.80 -2.60 -2.40 -2.20 --frames 100000 --max-err 200 --stop-per 2e-4 --seed 42 --workers 16 --part fs-bl42b
  echo "ALL DONE" ) > logs/run_fs-bl42b.out 2>&1
