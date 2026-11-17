#!/bin/bash
# fs-gv32b: FINAL blind VDE Link 32 (its own checkpoint NN, --cknn fmt), fresh seed 7032: -4.6, -4.2 [--charge-all: the NN's uncharged cells charged (small_rx ck_charge_all)]
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --snrs -4.6 --frames 60000 --seed 7032 --charge-all --part fs-gv32m46
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --snrs -4.2 --frames 200000 --seed 7032 --charge-all --part fs-gv32m42
  echo "ALL DONE" ) > logs/run_fs-gv32b.out 2>&1
