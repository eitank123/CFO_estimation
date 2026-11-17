#!/bin/bash
# fs-k13m02: ID 13 CALIBRATION packets at -0.2 (high-SNR end for the tuning), --calib, no cap
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_blind_fs.py --fmt id13 --design ga --cfo-max 0.03 --snrs -0.2 --frames 8000 --max-err 8000 --calib --seed 13 --workers 16 --dump --part fs-k13m02
  echo "ALL DONE" ) > logs/run_fs-k13m02.out 2>&1
