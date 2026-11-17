#!/bin/bash
# fs-gv32oc: FINAL blind VDE Link 32 (its own checkpoint NN, --cknn fmt), -3.8 dB, first half: seed 7032, 150000 frames [--charge-all: the NN's uncharged cells charged (small_rx ck_charge_all)] + jointly tuned + ONE phase hypothesis (nph 2): floor cut candidate
# (the second half, seed 7033, is fs-gv32d: disjoint packets, merge the two parts)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --snrs -3.8 --frames 150000 --seed 7032 --charge-all --sps '{"batch": null, "cores": 32, "final": 4, "win": 4.0, "ck_keep": 0.003, "ck_min": 4, "nph": {"0.15": [2, 0.5]}}' --part fs-gv32om38
  echo "ALL DONE" ) > logs/run_fs-gv32oc.out 2>&1
