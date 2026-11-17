#!/bin/bash
# fs-jv32c1: VDE-SAT 32 joint live tuning, CALIBRATION packets (--calib, seed 8032): base = NN c 3 + batch null + cores 32 (fair 32-core cost model) + final 16: batch (32, 5.0) + final 16 (final 16 alone on the old base)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --cknn fmt --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -6.2 --frames 1000 --batch 50 --seed 8032 --sps '{"final": 16}' --part fs-jv32c1m62
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --cknn fmt --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -5.8 --frames 2000 --batch 50 --seed 8032 --sps '{"final": 16}' --part fs-jv32c1m58
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --cknn fmt --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -5.4 --frames 8000 --batch 50 --seed 8032 --sps '{"final": 16}' --part fs-jv32c1m54
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --cknn fmt --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -5.0 --frames 30000 --seed 8032 --sps '{"final": 16}' --part fs-jv32c1m50
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --cknn fmt --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -4.6 --frames 60000 --seed 8032 --sps '{"final": 16}' --part fs-jv32c1m46
  echo "ALL DONE" ) > logs/run_fs-jv32c1.out 2>&1
