#!/bin/bash
# fs-jv32ub: LIVE check of the relative-objective tuner pick (joint_v32jr.json) on the calibration packets of fs-flv32b
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
A='--fmt vde32 --cfo-max 0.03 --cknn fmt --workers 16 --charge-all --dump --calib --max-err 1000000 --seed 8032'
SPS='{"batch": null, "cores": 32, "final": 4, "win": 4.0, "ck_keep": 0.003, "ck_min": 4}'
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py $A --sps "$SPS" --snrs -5.4 --frames 8000 --batch 50 --part fs-jv32ubm54
  $PY -u fullsys/run_blind_fs.py $A --sps "$SPS" --snrs -5.0 --frames 16000 --part fs-jv32ubm50
  echo "ALL DONE" ) > logs/run_fs-jv32ub.out 2>&1
