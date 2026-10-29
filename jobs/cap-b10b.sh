#!/bin/bash
# cap-b10b: bounded parallel decoders, blind R = 1/10: batches of 64 z 5, batches of 32 z 3 / 5
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_cap-b10b.out
$PY -u blind_ber.py --points 1/10:-5:16 1/10:-4:16 --max-frames 200 --min-errors 100000 --rx "S blind 1/10 best, batches of 64, z 5" "S blind 1/10 best, batches of 32, z 3" "S blind 1/10 best, batches of 32, z 5" --seed 5701 --part smoke-cap-b10b >> logs/run_cap-b10b.out 2>&1
echo "SMOKE DONE" >> logs/run_cap-b10b.out
