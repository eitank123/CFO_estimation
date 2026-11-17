#!/bin/bash
# fs-zt42k1: z-test live tuning ID 42b, CALIBRATION packets (--calib, seed 8042, paired over the fs-zt settings): fewer cells: NN shortlist 1 - 1e-2 (>= 4), z-test tau 0, kmin 4
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --cknn fmt --fmt id42b --fzstop 0.9,0.75 --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -4.0 --frames 12000 --seed 8042 --sps '{"ck_keep": 0.01, "ck_min": 4, "tau": {"2/5": 0.0}, "kmin": 4}' --part fs-zt42k1m40
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --cknn fmt --fmt id42b --fzstop 0.9,0.75 --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -3.8 --frames 80000 --seed 8042 --sps '{"ck_keep": 0.01, "ck_min": 4, "tau": {"2/5": 0.0}, "kmin": 4}' --part fs-zt42k1m38
  echo "ALL DONE" ) > logs/run_fs-zt42k1.out 2>&1
