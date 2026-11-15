#!/bin/bash
# bm2-smoke: the classic fine estimators (M&M + L&R, M&M + Fitz, Kay) and the split pilots with the estimated phase (ML, NN), R = 1/10 -5 dB, 3000 frames
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=small_cfo BLIND_STUDY=small_cfo CFO_MAX=0.03
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/logs small_cfo/results
: > logs/run_bm2-smoke.out
$PY -u polar_ber_experiment.py --mode ebn0 --packet 1024 --codes "R=0.1,C16" --sources "M&M, est. phase, pre-MF + CRC search (first pass)" "M&M + L&R, est. phase, pre-MF + CRC search (first pass)" "M&M + Fitz, est. phase, pre-MF + CRC search (first pass)" "Kay, est. phase, pre-MF + CRC search (first pass)" "Split pilots ML, est. phase, pre-MF + CRC search (first pass)" "Split pilots NN, est. phase, pre-MF + CRC search (first pass)" --shared-frames --tag bm2-smoke --extra-esn0 -5 --min-errors 1000 --max-frames 3000 --seed 18000 --workers 1 >> logs/run_bm2-smoke.out 2>&1
echo "SMOKE DONE" >> logs/run_bm2-smoke.out
