#!/bin/bash
# fs-uh42: --charge-all rerun of fs-h42 (same seeds, points, frames: decisions and BLER identical, only MACs). Was: FINAL blind ID 42, second seed at -3.8, -3.6 dB [JOINTLY TUNED settings: {"final": 8, "win": 4.0, "ck_keep": 0.003, "ck_min": 8}]
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 60 --cknn fmt --fmt id42b --fzstop 0.9,0.75 --snrs -3.8 --frames 30000 --seed 7142 --charge-all --sps '{"final": 8, "win": 4.0, "ck_keep": 0.003, "ck_min": 8}' --part fs-h42m38jt
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 60 --cknn fmt --fmt id42b --fzstop 0.9,0.75 --snrs -3.6 --frames 120000 --seed 7142 --charge-all --sps '{"final": 8, "win": 4.0, "ck_keep": 0.003, "ck_min": 8}' --part fs-h42m36jt
  echo "ALL DONE" ) > logs/run_fs-uh42.out 2>&1
