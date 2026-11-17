#!/bin/bash
# fs-k13m04: CALIBRATION packets for the ID 13 thresholds (--calib: seeds disjoint from the reported fs-c13* runs), Es/N0 -0.4, GA, chan intlv, no cap, early stops off, --dump
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_blind_fs.py --fmt id13 --design ga --snrs -0.4 --frames 4000 --max-err 4000 --calib --seed 13 --cfo-max 0.03 --workers 16 --dump --part fs-k13m04
  echo "ALL DONE" ) > logs/run_fs-k13m04.out 2>&1
