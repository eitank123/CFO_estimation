#!/bin/bash
# fs-jtv32g: replay of tuned pick + F5 (0.9, 0.75) on the calibration logs, to compare packet by packet with the live fs-jv32f*
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/joint_tune_fs.py --test fs-flv32am62 fs-flv32am58 fs-flv32bm54 fs-flv32bm50 fs-flv32cm46 --setting '{"cores": 32, "ck_min": 4, "win": 4.0, "final": 4, "ck_keep": 0.003, "fzstop": [0.9, 0.75]}' --name v32f5x --workers 8
  echo "ALL DONE" ) > logs/run_fs-jtv32g.out 2>&1
