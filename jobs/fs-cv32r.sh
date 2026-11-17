#!/bin/bash
# fs-cv32r: VDE-SAT 32 MAC cuts, CALIBRATION packets (--calib, seed 8032, paired with fs-cv32i / fs-cv32j = c 3, batch null + final 16): NN checkpoint c 1 + ck_min 4, low SNR
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --cknn fmt --ck-c 1 --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -6.2 --frames 1000 --batch 50 --seed 8032 --sps '{"batch": null, "final": 16, "ck_min": 4}' --part fs-cv32rm62
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --cknn fmt --ck-c 1 --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -5.8 --frames 2000 --batch 50 --seed 8032 --sps '{"batch": null, "final": 16, "ck_min": 4}' --part fs-cv32rm58
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --cknn fmt --ck-c 1 --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -5.4 --frames 8000 --batch 50 --seed 8032 --sps '{"batch": null, "final": 16, "ck_min": 4}' --part fs-cv32rm54
  echo "ALL DONE" ) > logs/run_fs-cv32r.out 2>&1
