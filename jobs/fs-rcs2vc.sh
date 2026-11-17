#!/bin/bash
# fs-rcs2vc: paired decoder variants (same seeds / batch as fs-rcs2v13 seed 13 and fs-rcs2v3 seed 3): ID 13 at -0.80 / -0.60 with log-MAP sf 1.0 and with ADAPTIVE sf-low-iters 2; ID 3 at -0.27 / -0.07 with log-MAP sf 1.0
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_rcs2.py --wf 13 --snrs -0.80 -0.60 --algo logmap --sf 1.0 --frames 1000000 --max-err 300 --seed 13 --workers 16 --part fs-rcs2vc13-lm
  $PY -u fullsys/run_rcs2.py --wf 13 --snrs -0.80 -0.60 --sf-low-iters 2 --frames 1000000 --max-err 300 --seed 13 --workers 16 --part fs-rcs2vc13-l2
  $PY -u fullsys/run_rcs2.py --wf 3 --snrs -0.27 -0.07 --algo logmap --sf 1.0 --frames 1000000 --max-err 300 --seed 3 --workers 16 --part fs-rcs2vc3-lm
  echo "ALL DONE" ) > logs/run_fs-rcs2vc.out 2>&1
