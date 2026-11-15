#!/bin/bash
# smoke-5: pilot-chosen phase branches (R = 1/10 search; R = 2/5, 1/2 fast path + search)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs
( while read -r line; do eval "$PY -u $line" & done < jobs/smoke5_cmds.txt; wait ) > logs/run_smoke-5.out 2>&1
