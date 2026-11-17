#!/bin/bash
# fs-ug42a: --charge-all rerun of fs-g42a (same seeds, points, frames: decisions and BLER identical, only MACs). Was: FINAL blind ID 42 (tuned F5 + retrained NN): -4.2 .. -3.6 [JOINTLY TUNED settings: {"final": 8, "win": 4.0, "ck_keep": 0.003, "ck_min": 8}]
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --fmt id42b --fzstop 0.9,0.75 --snrs -4.2 --frames 20000 --seed 7042 --charge-all --sps '{"final": 8, "win": 4.0, "ck_keep": 0.003, "ck_min": 8}' --part fs-g42m42jt
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --fmt id42b --fzstop 0.9,0.75 --snrs -4.0 --frames 20000 --seed 7042 --charge-all --sps '{"final": 8, "win": 4.0, "ck_keep": 0.003, "ck_min": 8}' --part fs-g42m40jt
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --fmt id42b --fzstop 0.9,0.75 --snrs -3.8 --frames 20000 --seed 7042 --charge-all --sps '{"final": 8, "win": 4.0, "ck_keep": 0.003, "ck_min": 8}' --part fs-g42m38jt
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --fmt id42b --fzstop 0.9,0.75 --snrs -3.6 --frames 60000 --seed 7042 --charge-all --sps '{"final": 8, "win": 4.0, "ck_keep": 0.003, "ck_min": 8}' --part fs-g42m36jt
  echo "ALL DONE" ) > logs/run_fs-ug42a.out 2>&1
