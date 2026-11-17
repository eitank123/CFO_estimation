#!/bin/bash
# fs-k3: ID 3 CALIBRATION packets at -0.8, -0.4 (--calib), no cap
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_blind_fs.py --fmt id3 --design ga --cfo-max 0.03 --snrs -0.8 -0.4 --frames 4000 --max-err 4000 --calib --seed 3 --workers 16 --dump --part fs-k3
  echo "ALL DONE" ) > logs/run_fs-k3.out 2>&1
