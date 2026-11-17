#!/bin/bash
# fs-zt3k3: z-test live tuning ID 3, CALIBRATION packets (--calib, seed 8003, paired over the fs-zt settings): earlier win: z > 4.5 (6) at a checkpoint decoded at once
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --cknn fmt --fmt id3 --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -0.6 --frames 20000 --seed 8003 --sps '{"win": 4.5}' --part fs-zt3k3m06
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --cknn fmt --fmt id3 --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -0.2 --frames 100000 --seed 8003 --sps '{"win": 4.5}' --part fs-zt3k3m02
  echo "ALL DONE" ) > logs/run_fs-zt3k3.out 2>&1
