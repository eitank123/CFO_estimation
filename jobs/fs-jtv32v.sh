#!/bin/bash
# fs-jtv32v: per-point replay of the relative-objective pick (final 4, win 4.0, ck_keep 0.003, ck_min 4) vs the live
# round-2 winner r3 (final 8, win 4.5, ck_keep 0.01, ck_min 4), on the calibration logs and the held-out (seed 8033) logs
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
CAL="fs-flv32am62 fs-flv32am58 fs-flv32bm54 fs-flv32bm50 fs-flv32cm46"
HO="fs-flv32tam62 fs-flv32tam58 fs-flv32tbm54 fs-flv32tbm50 fs-flv32tcm46"
PICK='{"cores": 32, "ck_min": 4, "win": 4.0, "final": 4, "ck_keep": 0.003}'
R3='{"cores": 32, "ck_min": 4, "win": 4.5, "final": 8, "ck_keep": 0.01}'
mkdir -p logs fullsys/results
(
  echo "=== PICK calib"; $PY -u fullsys/joint_tune_fs.py --test $CAL --setting "$PICK" --name v32vpc --workers 8
  echo "=== R3 calib";   $PY -u fullsys/joint_tune_fs.py --test $CAL --setting "$R3" --name v32vrc --workers 8
  echo "=== PICK heldout"; $PY -u fullsys/joint_tune_fs.py --test $HO --setting "$PICK" --name v32vph --workers 8
  echo "=== R3 heldout";   $PY -u fullsys/joint_tune_fs.py --test $HO --setting "$R3" --name v32vrh --workers 8
  echo "ALL DONE" ) > logs/run_fs-jtv32v.out 2>&1
