#!/bin/bash
# fs-t3nn: ID 3 with its RETRAINED checkpoint NN (--cknn fmt), paired with fs-c3m08 / fs-c3p00 / fs-d3p04 (seed 3)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --fmt id3 --snrs -0.8 --frames 20000 --seed 3 --cknn fmt --part fs-t3nnm08
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --fmt id3 --snrs 0.0 --frames 20000 --seed 3 --cknn fmt --part fs-t3nnp00
  $PY -u fullsys/run_blind_fs.py --design ga --cfo-max 0.03 --workers 16 --dump --max-err 30 --fmt id3 --snrs 0.4 --frames 80000 --seed 3 --cknn fmt --part fs-t3nnp04
  echo "ALL DONE" ) > logs/run_fs-t3nn.out 2>&1
