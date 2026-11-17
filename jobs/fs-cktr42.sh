#!/bin/bash
# fs-cktr42: the checkpoint NN retrained on id42b's own packets (fullsys/ck_nn_fs.py: its tx / rx, Es/N0 range CFG[id42b],
# seed tag + 900000); ~25 min budget on 16 cores -> small_cfo/blind/models/ck_nn_fs_id42b_c*.npz (run_blind_fs --cknn fmt)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results small_cfo/blind/models
( $PY -u fullsys/ck_nn_fs.py --fmt id42b --design ga --cfo-max 0.03 --budget 25 --part fs-cktr42
  echo "ALL DONE" ) > logs/run_fs-cktr42.out 2>&1
