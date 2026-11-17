#!/bin/bash
# fs-jv32g4: VDE-SAT 32 joint live tuning round 1, CALIBRATION packets (--calib, seed 8032; base = NN c 3 + batch null + final 16, control fs-cv32i / fs-cv32j): T_fine 3 (base 6)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --cknn fmt --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -6.2 --frames 1000 --batch 50 --seed 8032 --sps '{"batch": null, "final": 16, "T_fine": 3}' --part fs-jv32g4m62
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --cknn fmt --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -5.8 --frames 2000 --batch 50 --seed 8032 --sps '{"batch": null, "final": 16, "T_fine": 3}' --part fs-jv32g4m58
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --cknn fmt --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -5.4 --frames 8000 --batch 50 --seed 8032 --sps '{"batch": null, "final": 16, "T_fine": 3}' --part fs-jv32g4m54
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --cknn fmt --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -5.0 --frames 30000 --seed 8032 --sps '{"batch": null, "final": 16, "T_fine": 3}' --part fs-jv32g4m50
  echo "ALL DONE" ) > logs/run_fs-jv32g4.out 2>&1
