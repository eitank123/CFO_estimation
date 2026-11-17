#!/bin/bash
# fs-jv32uc: LIVE check of the relative-objective tuner pick (joint_v32jr.json) on the calibration packets of fs-flv32c
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
A='--fmt vde32 --cfo-max 0.03 --cknn fmt --workers 16 --charge-all --dump --calib --max-err 1000000 --seed 8032'
SPS='{"batch": null, "cores": 32, "final": 4, "win": 4.0, "ck_keep": 0.003, "ck_min": 4}'
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py $A --sps "$SPS" --snrs -4.6 --frames 20000 --part fs-jv32ucm46
  echo "ALL DONE" ) > logs/run_fs-jv32uc.out 2>&1
