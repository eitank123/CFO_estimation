#!/bin/bash
# fs-ztv32k3: z-test live tuning VDE-SAT 32, CALIBRATION packets (--calib, seed 8032, paired over the fs-zt settings): earlier win: z > 4.5 (6) at a checkpoint decoded at once
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --cknn fmt --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -5.4 --frames 8000 --batch 50 --seed 8032 --sps '{"win": 4.5}' --part fs-ztv32k3m54
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --cknn fmt --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -5.0 --frames 30000 --seed 8032 --sps '{"win": 4.5}' --part fs-ztv32k3m50
  echo "ALL DONE" ) > logs/run_fs-ztv32k3.out 2>&1
