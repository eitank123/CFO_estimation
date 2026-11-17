#!/bin/bash
# fs-uh13: --charge-all rerun of fs-h13 (same seeds, points, frames: decisions and BLER identical, only MACs). Was: FINAL blind ID 13, second seed at -0.6 dB (more errors) [JOINTLY TUNED settings: {"final": 16, "win": 4.5, "ck_keep": 0.003, "ck_min": 8}]
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 60 --cknn fmt --fmt id13 --fzstop 0.6,0.80 --snrs -0.6 --frames 50000 --seed 7113 --charge-all --sps '{"final": 16, "win": 4.5, "ck_keep": 0.003, "ck_min": 8}' --part fs-h13m06jt
  echo "ALL DONE" ) > logs/run_fs-uh13.out 2>&1
