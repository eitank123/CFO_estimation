#!/bin/bash
# fs-jtv32chk: joint tuner self-check (offline replay, no simulation) on the smoke full-search log fs-flv32smkm58
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/joint_tune_fs.py --calib fs-flv32smkm58 --check-only --name v32smk --workers 16
  echo "ALL DONE" ) > logs/run_fs-jtv32chk.out 2>&1
