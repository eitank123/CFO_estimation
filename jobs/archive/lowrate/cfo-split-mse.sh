#!/bin/bash
# CFO MSE of the split-pilot ML estimator (quarter layout), 512 and 1024 symbols: logs/cfo_split_mse.json
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_PILOTS=quarter
/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python -u cfo_split_mse.py --workers 16 > logs/run_cfo-split-mse.out 2>&1
