#!/bin/bash
# fs-nn3b: ID 3 with the checkpoint NN off at -0.8 and +0.4 dB, paired with fs-c3m08 / fs-d3p04 (seed 3)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --fmt id3 --snrs -0.8 --frames 20000 --seed 3 --cknn off --part fs-nn3m08
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --fmt id3 --snrs 0.4 --frames 80000 --seed 3 --cknn off --part fs-nn3p04
  echo "ALL DONE" ) > logs/run_fs-nn3b.out 2>&1
