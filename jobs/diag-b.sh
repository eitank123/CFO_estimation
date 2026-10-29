#!/bin/bash
# diag-b: blind final R = 1/10 lost BLER at -5 dB (1.0e-3 vs 1.8e-4): the join receiver without batches, batches of 32 z 5 / z 3, batches of 64 z 5 (grid step 4), 40000 packets each
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_diag-b.out
$PY -u blind_ber.py --points 1/10:-5:16 --max-frames 2500 --min-errors 100000 --rx "S blind 1/10 best, grid 4" "S blind final" "S blind final, batches of 32, z 3" "S blind final, batches of 64, z 5" --seed 5721 --part smoke-diag-b >> logs/run_diag-b.out 2>&1
echo "ALL DONE" >> logs/run_diag-b.out
