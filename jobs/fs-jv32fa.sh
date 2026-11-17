#!/bin/bash
# fs-jv32fa: LIVE cross-check of the F5 replay: tuned pick + F5 (q 0.9, t 0.75) on the calibration packets of fs-flv32a (compare with joint_tune_fs --test --setting, job fs-jtv32g)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
A='--fmt vde32 --cfo-max 0.03 --cknn fmt --workers 16 --charge-all --dump --calib --max-err 1000000 --seed 8032'
SPS='{"batch": null, "cores": 32, "final": 4, "win": 4.0, "ck_keep": 0.003, "ck_min": 4}'
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py $A --sps "$SPS" --snrs -6.2 --frames 2000 --batch 50 --fzstop 0.9,0.75 --part fs-jv32fam62
  $PY -u fullsys/run_blind_fs.py $A --sps "$SPS" --snrs -5.8 --frames 4000 --batch 50 --fzstop 0.9,0.75 --part fs-jv32fam58
  echo "ALL DONE" ) > logs/run_fs-jv32fa.out 2>&1
