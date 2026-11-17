#!/bin/bash
# fs-ug14c: --charge-all rerun of fs-g14c (same seeds, points, frames: decisions and BLER identical, only MACs). Was: FINAL blind ID 14 (tuned F5 + retrained NN) at 1.0 dB (top of the curve) [JOINTLY TUNED settings: {"final": 8, "win": 4.0, "ck_keep": 0.01, "ck_min": 4}]
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --fmt id14s --fzstop 0.7,0.78 --snrs 1.0 --frames 4000 --seed 7014 --charge-all --sps '{"final": 8, "win": 4.0, "ck_keep": 0.01, "ck_min": 4}' --part fs-g14p10jt
  echo "ALL DONE" ) > logs/run_fs-ug14c.out 2>&1
