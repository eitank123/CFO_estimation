#!/bin/bash
# diag-hi: blind R = 1/10 above -3 dB (BLER rising with SNR): old / new best receiver, and the new one with 4 phases; with the CRC-pass / check counters
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_diag-hi.out
$PY -u blind_ber.py --points 1/10:0:16 1/10:-1:16 1/10:-2:16 --max-frames 625 --min-errors 100000 --rx "S blind, checkpoints, coarse start, rescue + CRC" "S blind, checkpoints, coarse start, join top 16, phase hand-off, keep 2 phases, join top 8, rescue, tree cost + CRC" "S blind 1/10 best, 4 phases" --seed 5701 --part smoke-diag-hi >> logs/run_diag-hi.out 2>&1
echo "SMOKE DONE" >> logs/run_diag-hi.out
