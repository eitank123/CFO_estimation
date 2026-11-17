#!/bin/bash
# fs-zt3k1r (rerun of the parts lost in the 2026-11-17 Run:ai outage): z-test live tuning ID 3, CALIBRATION packets (--calib, seed 8003, paired over the fs-zt settings): fewer cells: NN shortlist 1 - 1e-2 (>= 4), z-test tau 0, kmin 4
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --cknn fmt --fmt id3 --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -0.2 --frames 100000 --seed 8003 --sps '{"ck_keep": 0.01, "ck_min": 4, "tau": {"2/5": 0.0}, "kmin": 4}' --part fs-zt3k1m02
  echo "ALL DONE" ) > logs/run_fs-zt3k1r.out 2>&1
