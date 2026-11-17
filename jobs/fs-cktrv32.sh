#!/bin/bash
# fs-cktrv32: the checkpoint NN retrained on vde32's own packets (fullsys/ck_nn_fs.py: its tx / rx, testing_s11g at the 0.15
# profile, Es/N0 -6.6 .. -3.8 = CFG[vde32], seed tag + 900000); ~25 min budget on 16 cores
# -> small_cfo/blind/models/ck_nn_fs_vde32_c*.npz (run_blind_fs --fmt vde32 --cknn fmt: c 3 = 1/4, --ck-c another)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results small_cfo/blind/models
( $PY -u fullsys/ck_nn_fs.py --fmt vde32 --cfo-max 0.03 --budget 25 --part fs-cktrv32
  echo "ALL DONE" ) > logs/run_fs-cktrv32.out 2>&1
