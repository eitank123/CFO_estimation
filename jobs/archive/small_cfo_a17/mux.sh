#!/bin/bash
# mux: time-multiplexed cores: the best receivers on 64 / 32 cores (passes, stored path metrics compared jointly) and the grader's top 128 cells on 64 / 32 cores
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_mux.out
$PY -u blind_ber.py --points 1/10:-5:16 1/10:-4:16 --max-frames 200 --min-errors 100000 --rx "S blind 1/10 best, 64 cores" "S blind 1/10 best, 32 cores" "S blind 1/10 best, top 128, 64 cores" "S blind 1/10 best, top 128, 32 cores" "S pilots 1/10 best, 64 cores" "S pilots 1/10 best, 32 cores" "S pilots 1/10 best, top 128, 64 cores" "S pilots 1/10 best, top 128, 32 cores" --seed 5701 --part smoke-mux10 >> logs/run_mux.out 2>&1
$PY -u blind_ber.py --points 2/5:0.5:16 --max-frames 200 --min-errors 100000 --rx "S blind checkpoint NN, 64 cores" "S blind checkpoint NN, 32 cores" "S blind z-test, top 128, 64 cores" "S blind z-test, top 128, 32 cores" "S pilots NN per rate, 64 cores" "S pilots NN per rate, 32 cores" "S pilots NN per rate, top 128, 32 cores" --seed 5702 --part smoke-mux25 >> logs/run_mux.out 2>&1
$PY -u blind_ber.py --points 1/2:2:16 --max-frames 200 --min-errors 100000 --rx "S blind checkpoint NN, 64 cores" "S blind checkpoint NN, 32 cores" "S blind z-test, top 128, 64 cores" "S blind z-test, top 128, 32 cores" "S pilots NN per rate, 64 cores" "S pilots NN per rate, 32 cores" "S pilots NN per rate, top 128, 32 cores" --seed 5703 --part smoke-mux2 >> logs/run_mux.out 2>&1
echo "SMOKE DONE" >> logs/run_mux.out
