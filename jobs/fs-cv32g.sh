#!/bin/bash
# fs-cv32g: VDE-SAT 32 MAC cuts, CALIBRATION packets (--calib, seed 8032, paired with fs-ztv32k0 / fs-cv32*): VDE NN control at -4.6 (fs-ztv32k0 has -5.4 / -5.0)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --cknn fmt --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -4.6 --frames 60000 --seed 8032 --part fs-cv32gm46
  echo "ALL DONE" ) > logs/run_fs-cv32g.out 2>&1
