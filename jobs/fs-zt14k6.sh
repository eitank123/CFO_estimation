#!/bin/bash
# fs-zt14k6: NN shortlist only: ck_keep 0.01, ck_min 4 (k1 without the tau and kmin change) (paired with fs-zt14k0)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --cknn fmt --fmt id14s --fzstop 0.7,0.78 --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs 1.4 --frames 10000 --seed 8014 --sps '{"ck_keep": 0.01, "ck_min": 4}' --part fs-zt14k6p14
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --cknn fmt --fmt id14s --fzstop 0.7,0.78 --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs 1.6 --frames 80000 --seed 8014 --sps '{"ck_keep": 0.01, "ck_min": 4}' --part fs-zt14k6p16
  echo "ALL DONE" ) > logs/run_fs-zt14k6.out 2>&1
