#!/bin/bash
# fs-jtv32n: joint tuning (relative objective) on the ONE-phase-guess full-search logs fs-flv32n*
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/joint_tune_fs.py --calib fs-flv32nam62 fs-flv32nam58 fs-flv32nbm54 fs-flv32nbm50 fs-flv32ncm46 --name v32jn --objective rel --restarts 2 --workers 8
  echo "ALL DONE" ) > logs/run_fs-jtv32n.out 2>&1
