#!/bin/bash
# fs-q3deep: DVB-RCS2 ID 3 own DA CFO estimate (+-0.03) deeper points (1e-5 region), matching blind's +0.6 / +0.8 dB
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/run_fullsys_da.py --sys rcs2 --frames 600000 --max-err 100 --variant strong --top-m 3 --workers 16 --wf 3 --snrs 0.33 0.53 --seed 303 --part fs-q3deep
  echo "ALL DONE" ) > logs/run_fs-q3deep.out 2>&1
