#!/bin/bash
# fs-zt13k9: JOINT round 2 (final 8, win 4.0, per-ID shortlist) (paired with fs-zt13k0)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --cknn fmt --fmt id13 --fzstop 0.6,0.80 --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -0.8 --frames 10000 --seed 8013 --sps '{"final": 8, "win": 4.0, "ck_keep": 0.003, "ck_min": 8}' --part fs-zt13k9m08
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --cknn fmt --fmt id13 --fzstop 0.6,0.80 --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -0.6 --frames 40000 --seed 8013 --sps '{"final": 8, "win": 4.0, "ck_keep": 0.003, "ck_min": 8}' --part fs-zt13k9m06
  echo "ALL DONE" ) > logs/run_fs-zt13k9.out 2>&1
