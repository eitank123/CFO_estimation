#!/bin/bash
# fs-cv32h: VDE-SAT 32 MAC cuts, CALIBRATION packets (--calib, seed 8032, paired with fs-cv32* / fs-ztv32*): VDE NN control, low SNR
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --cknn fmt --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -6.6 --frames 1000 --batch 50 --seed 8032 --part fs-cv32hm66
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --cknn fmt --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -6.2 --frames 1000 --batch 50 --seed 8032 --part fs-cv32hm62
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --cknn fmt --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -5.8 --frames 2000 --batch 50 --seed 8032 --part fs-cv32hm58
  echo "ALL DONE" ) > logs/run_fs-cv32h.out 2>&1
