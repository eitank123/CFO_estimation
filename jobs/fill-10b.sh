#!/bin/bash
# fill-10b: best blind (coarse start + checkpoints + rescue) at the missing SNRs, R = 1/10 -4..0 dB (plots)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_fill-10b.out
$PY -u blind_ber.py --points 1/10:-4:4 1/10:-3:4 1/10:-2:4 1/10:-1:4 1/10:0:4 --rx "S blind, checkpoints, coarse start, rescue + CRC" --seed 5701 --max-frames 25000 --min-errors 100 --part fill-10b >> logs/run_fill-10b.out 2>&1
