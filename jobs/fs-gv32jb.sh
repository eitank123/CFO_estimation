#!/bin/bash
# fs-gv32jb: FINAL blind VDE Link 32 (its own checkpoint NN, --cknn fmt), fresh seed 7032: -4.6, -4.2 [--charge-all: the NN's uncharged cells charged (small_rx ck_charge_all)] + JOINTLY TUNED pick (joint_v32j.json): batch null, cores 32, final 0, win 4.0, ck_keep 0.003, ck_min 4
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --snrs -4.6 --frames 60000 --seed 7032 --charge-all --sps '{"batch": null, "cores": 32, "final": 0, "win": 4.0, "ck_keep": 0.003, "ck_min": 4}' --part fs-gv32jm46
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --snrs -4.2 --frames 200000 --seed 7032 --charge-all --sps '{"batch": null, "cores": 32, "final": 0, "win": 4.0, "ck_keep": 0.003, "ck_min": 4}' --part fs-gv32jm42
  echo "ALL DONE" ) > logs/run_fs-gv32jb.out 2>&1
