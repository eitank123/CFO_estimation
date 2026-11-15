#!/bin/bash
# fp-1 (smoke slot): data-aided consistency checks against the staircase false passes (forced wrong-peak decodes)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/results
( $PY -u blind/smoke/fp_check.py --points 2/5:0.5:16000 2/5:1:24000 --tag r25
  $PY -u blind/smoke/fp_check.py --points 1/10:-5:16000 1/10:-4:16000 --tag r10 ) > logs/run_fp-1.out 2>&1
