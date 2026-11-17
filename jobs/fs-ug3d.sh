#!/bin/bash
# fs-ug3d: --charge-all rerun of fs-g3d (same seeds, points, frames: decisions and BLER identical, only MACs). Was: FINAL blind ID 3 (retrained NN) at -0.8 and -0.4 dB (fill-in points) [JOINTLY TUNED settings: {"final": 8, "win": 4.5}]
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --fmt id3 --snrs -0.8 --frames 20000 --seed 7003 --charge-all --sps '{"final": 8, "win": 4.5}' --part fs-g3m08jt
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --fmt id3 --snrs -0.4 --frames 20000 --seed 7003 --charge-all --sps '{"final": 8, "win": 4.5}' --part fs-g3m04jt
  echo "ALL DONE" ) > logs/run_fs-ug3d.out 2>&1
