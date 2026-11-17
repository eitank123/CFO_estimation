#!/bin/bash
# fs-nn3: ID 3 with the checkpoint NN off (z-test only; the NN was trained on 1024-symbol packets): paired with fs-c3m04 / fs-c3p00
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --fmt id3 --snrs -0.4 --frames 20000 --seed 3 --cknn off --part fs-nn3m04
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --fmt id3 --snrs 0.0 --frames 20000 --seed 3 --cknn off --part fs-nn3p00
  echo "ALL DONE" ) > logs/run_fs-nn3.out 2>&1
