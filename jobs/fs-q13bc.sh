#!/bin/bash
# fs-q13bc: FAST ID 13: blind smoke (100 packets) then CALIBRATION packets (--calib, disjoint seeds) for the ID 13 thresholds
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_blind_fs.py --fmt id13 --snrs -1.2 --frames 100 --max-err 100 --seed 990 --workers 16 --dump --part fs-q13bc-smoke
  $PY -u fullsys/run_blind_fs.py --fmt id13 --snrs -0.8 -0.4 --frames 4000 --max-err 4000 --calib --dump --seed 7013 --workers 16 --part fs-q13bc-cal
  echo "ALL DONE" ) > logs/run_fs-q13bc.out 2>&1
