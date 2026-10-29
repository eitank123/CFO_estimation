#!/bin/bash
# cap-25: bounded parallel decoders, R = 2/5 0.5 dB and R = 1/2 2 dB: blind z-test / checkpoint NN baselines, top 64 / 32, batches; pilots NN per rate, top 64 / 32
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_cap-25.out
$PY -u blind_ber.py --points 2/5:0.5:16 --max-frames 200 --min-errors 100000 --rx "S blind, checkpoints, checkpoint NN, rescue, tree cost + CRC" "S blind, checkpoints, rescue, tree cost + CRC" "S blind z-test, top 64" "S blind z-test, top 32" "S blind z-test, batches of 64, z 3" "S blind z-test, batches of 64, z 5" "S blind z-test, batches of 32, z 3" "S blind z-test, batches of 32, z 5" "S pilots N3x8, checkpoints, pilot score, NN per rate, rescue + CRC" "S pilots NN per rate, top 64" "S pilots NN per rate, top 32" --seed 5702 --part smoke-cap-25 >> logs/run_cap-25.out 2>&1
$PY -u blind_ber.py --points 1/2:2:16 --max-frames 200 --min-errors 100000 --rx "S blind, checkpoints, checkpoint NN, rescue, tree cost + CRC" "S blind, checkpoints, rescue, tree cost + CRC" "S blind z-test, top 64" "S blind z-test, top 32" "S blind z-test, batches of 64, z 3" "S blind z-test, batches of 64, z 5" "S blind z-test, batches of 32, z 3" "S blind z-test, batches of 32, z 5" "S pilots N3x8, checkpoints, pilot score, NN per rate, rescue + CRC" "S pilots NN per rate, top 64" "S pilots NN per rate, top 32" --seed 5703 --part smoke-cap-2 >> logs/run_cap-25.out 2>&1
echo "SMOKE DONE" >> logs/run_cap-25.out
