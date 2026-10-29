#!/bin/bash
# sclt-a: CA-SCL-8 path-metric trajectories of the refinement hypotheses (parallel SCL with pruning), small-CFO study
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
$PY -u blind/smoke/scl_traj.py --points 1/10:-5:1600 2/5:0.5:4800 1/2:2:8000 --tag a > logs/run_sclt-a.out 2>&1
