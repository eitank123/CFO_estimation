#!/bin/bash
# crit-25: R = 2/5 0.5 dB and R = 1/2 2 dB with the critical-path MAC count: the best receivers all at once, on 64 / 32 cores in passes, blind in batches of 64 / 32
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_crit-25.out
$PY -u blind_ber.py --points 2/5:0.5:16 --max-frames 200 --min-errors 100000 --rx "S blind, checkpoints, checkpoint NN, rescue, tree cost + CRC" "S blind checkpoint NN, 64 cores" "S blind checkpoint NN, 32 cores" "S blind z-test, batches of 64, z 3" "S blind z-test, batches of 64, z 5" "S blind z-test, batches of 32, z 3" "S blind z-test, batches of 32, z 5" "S pilots N3x8, checkpoints, pilot score, NN per rate, rescue + CRC" "S pilots NN per rate, 64 cores" "S pilots NN per rate, 32 cores" --seed 5702 --part smoke-crit-25 >> logs/run_crit-25.out 2>&1
$PY -u blind_ber.py --points 1/2:2:16 --max-frames 200 --min-errors 100000 --rx "S blind, checkpoints, checkpoint NN, rescue, tree cost + CRC" "S blind checkpoint NN, 64 cores" "S blind checkpoint NN, 32 cores" "S blind z-test, batches of 64, z 3" "S blind z-test, batches of 64, z 5" "S blind z-test, batches of 32, z 3" "S blind z-test, batches of 32, z 5" "S pilots N3x8, checkpoints, pilot score, NN per rate, rescue + CRC" "S pilots NN per rate, 64 cores" "S pilots NN per rate, 32 cores" --seed 5703 --part smoke-crit-2 >> logs/run_crit-25.out 2>&1
echo "SMOKE DONE" >> logs/run_crit-25.out
