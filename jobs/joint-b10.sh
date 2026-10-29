#!/bin/bash
# joint-b10: joint CA-SCL of the candidates (32 / 16 / 8 shared paths) vs one at a time, blind R = 1/10 batches of 32; + CRC-only undetected errors and the list-parallel critical path
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_joint-b10.out
$PY -u blind_ber.py --points 1/10:-5:16 1/10:-4:16 --max-frames 200 --min-errors 100000 --rx "S blind 1/10 best, batches of 32, z 5" "S blind 1/10 best, batches of 32, z 5, joint L32" "S blind 1/10 best, batches of 32, z 5, joint L16" "S blind 1/10 best, batches of 32, z 5, joint L8" --seed 5701 --part smoke-joint-b10 >> logs/run_joint-b10.out 2>&1
echo "SMOKE DONE" >> logs/run_joint-b10.out
