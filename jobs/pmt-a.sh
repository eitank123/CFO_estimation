#!/bin/bash
# pmt-a: partial path metrics along the decode (checkpoint pruning / early stop of the CFO search), small-CFO study
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
$PY -u blind/smoke/pm_traj.py --points 1/10:-5:4000 2/5:0.5:4000 1/2:2:4000 --tag a > logs/run_pmt-a.out 2>&1
