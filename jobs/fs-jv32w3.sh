#!/bin/bash
# fs-jv32w3: VDE MAC-floor cut on top of the jointly tuned receiver, calibration packets (paired with fs-jv32u* / fs-flv32*): NN checkpoint 3/16 (c 2)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
A='--fmt vde32 --cfo-max 0.03 --cknn fmt --ck-c 2 --workers 16 --charge-all --dump --calib --max-err 1000000 --seed 8032'
SPS='{"batch": null, "cores": 32, "final": 4, "win": 4.0, "ck_keep": 0.003, "ck_min": 4}'
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py $A --sps "$SPS" --snrs -6.2 --frames 2000 --batch 50 --part fs-jv32w3m62
  $PY -u fullsys/run_blind_fs.py $A --sps "$SPS" --snrs -5.4 --frames 8000 --batch 50 --part fs-jv32w3m54
  $PY -u fullsys/run_blind_fs.py $A --sps "$SPS" --snrs -4.6 --frames 20000 --part fs-jv32w3m46
  echo "ALL DONE" ) > logs/run_fs-jv32w3.out 2>&1
