#!/bin/bash
# fs-k3b: blind ID 3 calibration packets (disjoint seeds) at the high-SNR end where the first ID 3 tuning lost packets
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --frames 12000 --max-err 12000 --calib --workers 16 --dump --fmt id3 --snrs -0.2 0.0 0.2 --seed 33 --part fs-k3b
  echo "ALL DONE" ) > logs/run_fs-k3b.out 2>&1
