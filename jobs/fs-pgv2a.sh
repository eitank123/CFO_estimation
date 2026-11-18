#!/bin/bash
# fs-pgv2a: code-only genie-sync reference for VDE-SAT Link 32 (turbo vs polar, genie vs genie): rate-matched polar A 280, E 1269, N 2048 puncture, PW design (as the blind VDE receiver), CRC-32, CA-SCL-8, BPSK, genie sync; part a of 2
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_polar_genie.py --fmt vde32 --list 8 --snrs -5.40 -5.20 -5.00 -4.80 --frames 300000 --max-err 100 --stop-per 1e-4 --seed 321 --workers 16 --part fs-pgv2a
  echo "ALL DONE" ) > logs/run_fs-pgv2a.out 2>&1
