#!/bin/bash
# ckr-smoke: the checkpoint NN inside the small-CFO search (small_rx ck_nn), short BLER run against the same receivers
# without it: pilots (H + rescue) at R = 1/10 -5 dB, blind (checkpoints + rescue) at R = 2/5 0.5 dB and R = 1/2 2 dB
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_ckr-smoke.out
P="S pilots N3x8, checkpoints, pilot score"
Bl="S blind, checkpoints"
$PY -u blind_ber.py --points 1/10:-5:16 --max-frames 150 --min-errors 100 --rx "$P, rescue + CRC" "$P, checkpoint NN, rescue + CRC" "$P, checkpoint NN + early stop, rescue + CRC" --seed 5701 --part smoke-ckr10 >> logs/run_ckr-smoke.out 2>&1
$PY -u blind_ber.py --points 2/5:0.5:16 1/2:2:16 --max-frames 150 --min-errors 100 --rx "$Bl, rescue + CRC" "$Bl, checkpoint NN, rescue + CRC" "$Bl, checkpoint NN + early stop, rescue + CRC" --seed 5702 --part smoke-ckr25 >> logs/run_ckr-smoke.out 2>&1
echo "SMOKE DONE" >> logs/run_ckr-smoke.out
