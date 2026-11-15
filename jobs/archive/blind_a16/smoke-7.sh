#!/bin/bash
# smoke-7: pilot-direct first try at R = 1/10
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs
( while read -r line; do eval "$PY -u $line" & done < jobs/smoke7_cmds.txt; wait ) > logs/run_smoke-7.out 2>&1
