#!/bin/bash
# fs-zt42k8: JOINT combination (final 16 + win 4.5 + the per-ID shortlist that passed k6/k7) (paired with fs-zt42k0)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --cknn fmt --fmt id42b --fzstop 0.9,0.75 --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -4.0 --frames 12000 --seed 8042 --sps '{"final": 16, "win": 4.5, "ck_keep": 0.003, "ck_min": 8}' --part fs-zt42k8m40
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --cknn fmt --fmt id42b --fzstop 0.9,0.75 --workers 16 --charge-all --dump --calib --max-err 1000000 --snrs -3.8 --frames 80000 --seed 8042 --sps '{"final": 16, "win": 4.5, "ck_keep": 0.003, "ck_min": 8}' --part fs-zt42k8m38
  echo "ALL DONE" ) > logs/run_fs-zt42k8.out 2>&1
