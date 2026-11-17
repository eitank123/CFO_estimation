#!/bin/bash
# fs-vda32lo: VDE Link 32 own DA CFO estimate, waterfall below -5 dB
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_fullsys_da.py --sys vde --link 32 --snrs -7.0 -6.5 -6.0 -5.5 --frames 100000 --max-err 100 --seed 1 --variant strong --top-m 3 --algo logmap --workers 16 --part fs-vda32lo
  echo "ALL DONE" ) > logs/run_fs-vda32lo.out 2>&1
