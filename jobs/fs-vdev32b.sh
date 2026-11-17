#!/bin/bash
# fs-vdev32b: VDE-SAT Link 32, log-MAP with up to 16 iterations and CRC early stop, same grid / seed / batch as fs-vdev32
# (paired packets with its log-MAP 8 it. and max-log parts). Memory: 32Gi.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_vde.py --link 32 --snrs -7.0 -6.5 -6.0 -5.5 -5.0 -4.5 -4.0 -3.5 -3.0 --frames 1000000 --max-err 300 --seed 1 --workers 16 --algo logmap --iters 16 --part fs-vdev32b
  echo "ALL DONE" ) > logs/run_fs-vdev32b.out 2>&1
