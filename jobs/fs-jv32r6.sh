#!/bin/bash
# fs-jv32r6: VDE-SAT 32 joint live round 3 around r3, CALIBRATION packets (--calib, seed 8032), control fs-jv32c0 / fs-jv32r3: r3 + ncand 2
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --cknn fmt --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -6.2 --frames 1000 --batch 50 --seed 8032 --sps '{"batch": null, "cores": 32, "win": 4.5, "ck_keep": 0.01, "final": 8, "ck_min": 4, "ncand": 2}' --part fs-jv32r6m62
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --cknn fmt --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -5.8 --frames 2000 --batch 50 --seed 8032 --sps '{"batch": null, "cores": 32, "win": 4.5, "ck_keep": 0.01, "final": 8, "ck_min": 4, "ncand": 2}' --part fs-jv32r6m58
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --cknn fmt --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -5.4 --frames 8000 --batch 50 --seed 8032 --sps '{"batch": null, "cores": 32, "win": 4.5, "ck_keep": 0.01, "final": 8, "ck_min": 4, "ncand": 2}' --part fs-jv32r6m54
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --cknn fmt --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -5.0 --frames 30000 --seed 8032 --sps '{"batch": null, "cores": 32, "win": 4.5, "ck_keep": 0.01, "final": 8, "ck_min": 4, "ncand": 2}' --part fs-jv32r6m50
  $PY -u fullsys/run_blind_fs.py --fmt vde32 --cfo-max 0.03 --cknn fmt --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -4.6 --frames 60000 --seed 8032 --sps '{"batch": null, "cores": 32, "win": 4.5, "ck_keep": 0.01, "final": 8, "ck_min": 4, "ncand": 2}' --part fs-jv32r6m46
  echo "ALL DONE" ) > logs/run_fs-jv32r6.out 2>&1
