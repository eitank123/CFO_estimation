#!/bin/bash
# fs-g3d: FINAL blind ID 3 (retrained NN) at -0.8 and -0.4 dB (fill-in points)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --fmt id3 --snrs -0.8 --frames 20000 --seed 7003 --part fs-g3m08
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --cknn fmt --fmt id3 --snrs -0.4 --frames 20000 --seed 7003 --part fs-g3m04
  echo "ALL DONE" ) > logs/run_fs-g3d.out 2>&1
