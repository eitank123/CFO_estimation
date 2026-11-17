#!/bin/bash
# fs-pgvde: rate-matched polar (A 280, E 1269, N 2048 puncture, CRC-32, CA-SCL-8), BPSK (SF 8 spreading not simulated: same Es/N0 per symbol in genie AWGN), genie sync, vs VDE-SAT Link 32 (M.2092 -4.5 dB); no point below -5 dB
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_polar_genie.py --fmt vde32 --snrs -5.00 -4.80 -4.60 -4.40 -4.20 -4.00 -3.80 -3.60 -3.40 -3.20 -3.00 -2.80 -2.60 -2.40 --frames 1000000 --max-err 300 --stop-per 5e-5 --seed 32 --workers 16 --part fs-pgvde
  echo "ALL DONE" ) > logs/run_fs-pgvde.out 2>&1
