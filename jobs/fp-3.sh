#!/bin/bash
# fp-3 (smoke slot): normalised re-encoding correlation of right vs false passes at the remaining SNRs (threshold table)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/results
( $PY -u blind/smoke/fp_check.py --points 1/10:-3:16000 1/10:-2:16000 1/10:-1:16000 1/10:0:16000 --tag r10b
  $PY -u blind/smoke/fp_check.py --points 2/5:1.5:16000 2/5:2:16000 1/2:2:16000 1/2:3:16000 --tag r25b ) > logs/run_fp-3.out 2>&1
