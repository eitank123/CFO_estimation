#!/bin/bash
# bf-25: blind R = 2/5 best-first (the 4th-power periodogram's best 32 / 16 cells first) and the 4-peak fast path on the
# checkpoint-NN receiver, tree cost, full statistics at 0.5 / 1 dB with the same receiver unchanged (paired seeds)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_bf-25.out
N="S blind, checkpoints, checkpoint NN"
$PY -u blind_ber.py --points 2/5:0.5:8 2/5:1:8 --max-frames 50000 --min-errors 100 --rx "$N, rescue, tree cost + CRC" "$N, best-first 32, rescue, tree cost + CRC" "$N, best-first 16, rescue, tree cost + CRC" "$N, best-first 32, 4-peak fast path, rescue, tree cost + CRC" --seed 5702 --part bf-25 >> logs/run_bf-25.out 2>&1
