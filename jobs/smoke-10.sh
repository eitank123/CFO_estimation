#!/bin/bash
# smoke-10: pilot-chosen 2 of 4 phases in the R = 1/10 search
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs
( while read -r line; do eval "$PY -u $line" & done < jobs/smoke10_cmds.txt; wait ) > logs/run_smoke-10.out 2>&1
