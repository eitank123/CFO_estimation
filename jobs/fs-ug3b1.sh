#!/bin/bash
# fs-ug3b1: --charge-all rerun of fs-g3b (part 1 of 2: +0.2, +0.4, +0.6; same seeds, points, frames: decisions and BLER identical, only MACs) [JOINTLY TUNED settings: {"final": 8, "win": 4.5}]
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --fmt id3 --snrs 0.2 --frames 60000 --seed 7003 --charge-all --sps '{"final": 8, "win": 4.5}' --part fs-g3p02jt
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --fmt id3 --snrs 0.4 --frames 100000 --seed 7003 --charge-all --sps '{"final": 8, "win": 4.5}' --part fs-g3p04jt
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --fmt id3 --snrs 0.6 --frames 150000 --seed 7003 --charge-all --sps '{"final": 8, "win": 4.5}' --part fs-g3p06jt
  echo "ALL DONE" ) > logs/run_fs-ug3b1.out 2>&1
