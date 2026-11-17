#!/bin/bash
# fs-jtv32h: held-out replay of the joint tuner's pick on the seed-8033 full-search logs fs-flv32t* (never used in the search)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/joint_tune_fs.py --test fs-flv32tam62 fs-flv32tam58 fs-flv32tbm54 fs-flv32tbm50 fs-flv32tcm46 --setting '{"cores": 32, "ck_min": 4, "win": 4.0, "final": 0, "ck_keep": 0.003}' --name v32jh --workers 8
  echo "ALL DONE" ) > logs/run_fs-jtv32h.out 2>&1
