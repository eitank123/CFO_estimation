#!/bin/bash
# fs-jv32x5: VDE operating-point statistics, FRESH seed 7034 (paired tuned vs one phase guess): tuned, -4.6 dB
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
A='--fmt vde32 --cfo-max 0.03 --cknn fmt --workers 16 --charge-all --dump --max-err 1000000 --seed 7034'
SPS='{"batch": null, "cores": 32, "final": 4, "win": 4.0, "ck_keep": 0.003, "ck_min": 4}'
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py $A --sps "$SPS" --snrs -4.6 --frames 60000 --part fs-jv32x5m46
  echo "ALL DONE" ) > logs/run_fs-jv32x5.out 2>&1
