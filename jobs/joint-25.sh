#!/bin/bash
# joint-25: joint CA-SCL of the candidates, R = 2/5 0.5 dB and R = 1/2 2 dB (blind checkpoint NN / pilots NN per rate, 32 cores)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_joint-25.out
$PY -u blind_ber.py --points 2/5:0.5:16 --max-frames 200 --min-errors 100000 --rx "S blind checkpoint NN, 32 cores" "S blind checkpoint NN, 32 cores, joint L32" "S blind checkpoint NN, 32 cores, joint L16" "S blind checkpoint NN, 32 cores, joint L8" "S pilots NN per rate, 32 cores" "S pilots NN per rate, 32 cores, joint L32" "S pilots NN per rate, 32 cores, joint L16" "S pilots NN per rate, 32 cores, joint L8" --seed 5702 --part smoke-joint-25 >> logs/run_joint-25.out 2>&1
$PY -u blind_ber.py --points 1/2:2:16 --max-frames 200 --min-errors 100000 --rx "S blind checkpoint NN, 32 cores" "S blind checkpoint NN, 32 cores, joint L32" "S blind checkpoint NN, 32 cores, joint L16" "S blind checkpoint NN, 32 cores, joint L8" "S pilots NN per rate, 32 cores" "S pilots NN per rate, 32 cores, joint L32" "S pilots NN per rate, 32 cores, joint L16" "S pilots NN per rate, 32 cores, joint L8" --seed 5703 --part smoke-joint-2 >> logs/run_joint-25.out 2>&1
echo "SMOKE DONE" >> logs/run_joint-25.out
