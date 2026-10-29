#!/bin/bash
# smoke-11: left-metric screening + adaptive phases in the R = 1/10 search below -2 dB
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs
( while read -r line; do eval "$PY -u $line" & done < jobs/smoke11_cmds.txt; wait ) > logs/run_smoke-11.out 2>&1
