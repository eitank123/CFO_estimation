#!/bin/bash
# fs-jtv32a: VDE-SAT 32 JOINT TUNING (offline replay of the full-search logs fs-flv32a/b/c, calibration seed 8032):
# self-check first (aborts on mismatch), then coordinate descent + 2 restarts, objective mean of per-point mean MACs/core
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/joint_tune_fs.py --calib fs-flv32am62 fs-flv32am58 fs-flv32bm54 fs-flv32bm50 fs-flv32cm46 --check-only --name v32chk --workers 16 && \
  $PY -u fullsys/joint_tune_fs.py --calib fs-flv32am62 fs-flv32am58 fs-flv32bm54 fs-flv32bm50 fs-flv32cm46 --name v32j --restarts 2 --workers 16
  echo "ALL DONE" ) > logs/run_fs-jtv32a.out 2>&1
