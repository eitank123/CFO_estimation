#!/bin/bash
# fs-blvde: blind (adopted 0.15 receiver testing_s11g, spec11 off: provisional, bpsk_sq) on VDE-SAT Link 32 BPSK (A 280, E 1269, N 2048 puncture; SF 8 not simulated); paired with fs-pgvde (seed 32)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_blind_fs.py --fmt vde32 --snrs -4.60 -4.40 -4.20 -4.00 -3.80 -3.60 -3.40 -3.20 -3.00 -2.80 -2.60 -2.40 -2.20 -2.00 --frames 100000 --max-err 200 --stop-per 2e-4 --seed 32 --workers 16 --part fs-blvde
  echo "ALL DONE" ) > logs/run_fs-blvde.out 2>&1
