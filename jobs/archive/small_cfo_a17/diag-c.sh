#!/bin/bash
# diag-c: blind R = 1/10 -5 dB, 40000 packets each: the old coarse start (both neighbours, every phase) in batches of 32 (grid step 4), and with each of the cheaper join steps alone
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_diag-c.out
$PY -u blind_ber.py --points 1/10:-5:16 --max-frames 2500 --min-errors 100000 --rx "S blind C, batches of 32" "S blind C, batches of 32, join top 16 + hand-off" "S blind C, batches of 32, keep 2 phases" "S blind C, batches of 32, join top 8" --seed 5721 --part smoke-diag-c >> logs/run_diag-c.out 2>&1
echo "ALL DONE" >> logs/run_diag-c.out
