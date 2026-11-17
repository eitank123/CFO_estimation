#!/bin/bash
# fs-zt3k6: NN shortlist only: ck_keep 0.01, ck_min 4 (k1 without the tau and kmin change) (paired with fs-zt3k0)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --cknn fmt --fmt id3 --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -0.6 --frames 20000 --seed 8003 --sps '{"ck_keep": 0.01, "ck_min": 4}' --part fs-zt3k6m06
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --cknn fmt --fmt id3 --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -0.2 --frames 100000 --seed 8003 --sps '{"ck_keep": 0.01, "ck_min": 4}' --part fs-zt3k6m02
  echo "ALL DONE" ) > logs/run_fs-zt3k6.out 2>&1
