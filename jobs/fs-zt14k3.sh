#!/bin/bash
# fs-zt14k3: z-test live tuning ID 14s, CALIBRATION packets (--calib, seed 8014, paired over the fs-zt settings): earlier win: z > 4.5 (6) at a checkpoint decoded at once
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --cknn fmt --fmt id14s --fzstop 0.7,0.78 --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs 1.4 --frames 10000 --seed 8014 --sps '{"win": 4.5}' --part fs-zt14k3p14
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --cknn fmt --fmt id14s --fzstop 0.7,0.78 --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs 1.6 --frames 80000 --seed 8014 --sps '{"win": 4.5}' --part fs-zt14k3p16
  echo "ALL DONE" ) > logs/run_fs-zt14k3.out 2>&1
