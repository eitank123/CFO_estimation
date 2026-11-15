#!/bin/bash
# fp15a: re-encoding threshold (RHO_N) calibration for R = 0.15, as fp-1 / fp-3 for R = 1/10
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/results
$PY -u blind/smoke/fp_check.py --points 0.15:-4.5:16000 0.15:-4:16000 0.15:-3:16000 0.15:-2:16000 --tag r15a > logs/run_fp15a.out 2>&1
