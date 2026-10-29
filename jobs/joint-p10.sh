#!/bin/bash
# joint-p10: joint CA-SCL of the candidates, pilots R = 1/10 (batches of 32 / 32 cores)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_joint-p10.out
$PY -u blind_ber.py --points 1/10:-5:16 1/10:-4:16 --max-frames 200 --min-errors 100000 --rx "S pilots 1/10 best, batches of 32, z 3" "S pilots 1/10 best, batches of 32, z 3, joint L32" "S pilots 1/10 best, batches of 32, z 3, joint L16" "S pilots 1/10 best, batches of 32, z 3, joint L8" "S pilots 1/10 best, 32 cores" "S pilots 1/10 best, 32 cores, joint L32" "S pilots 1/10 best, 32 cores, joint L16" "S pilots 1/10 best, 32 cores, joint L8" --seed 5701 --part smoke-joint-p10 >> logs/run_joint-p10.out 2>&1
echo "SMOKE DONE" >> logs/run_joint-p10.out
