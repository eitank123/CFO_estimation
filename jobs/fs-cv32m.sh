#!/bin/bash
# fs-cv32m: VDE-SAT 32 MAC cuts, CALIBRATION packets (--calib, seed 8032, paired with fs-cv32* / fs-ztv32*): no NN control, low SNR (two-pass replay)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --cknn keep --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -6.6 --frames 1000 --batch 50 --seed 8032 --part fs-cv32mm66
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --cknn keep --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -6.2 --frames 1000 --batch 50 --seed 8032 --part fs-cv32mm62
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --cknn keep --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -5.8 --frames 2000 --batch 50 --seed 8032 --part fs-cv32mm58
  echo "ALL DONE" ) > logs/run_fs-cv32m.out 2>&1
