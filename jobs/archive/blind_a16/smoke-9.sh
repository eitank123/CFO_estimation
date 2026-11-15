#!/bin/bash
# smoke-9: no statistics for the pilot search, no code-aided retry in the fast path
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs
( while read -r line; do eval "$PY -u $line" & done < jobs/smoke9_cmds.txt; wait ) > logs/run_smoke-9.out 2>&1
