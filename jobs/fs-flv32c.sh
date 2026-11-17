#!/bin/bash
# fs-flv32c: VDE-SAT 32 full-search log (small_rx fulllog, fullsys/joint_tune_fs.py), CALIBRATION packets (--calib, seed 8032), base NN c 3 + batch null, cores 32, final 16: -4.6 dB
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
A='--fmt vde32 --cfo-max 0.03 --cknn fmt --workers 16 --charge-all --dump --fulllog --calib --max-err 1000000 --seed 8032'
SPS='{"batch": null, "cores": 32, "final": 16}'
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py $A --sps "$SPS" --snrs -4.6 --frames 20000 --part fs-flv32cm46
  echo "ALL DONE" ) > logs/run_fs-flv32c.out 2>&1
