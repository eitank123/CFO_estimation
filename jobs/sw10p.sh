#!/bin/bash
# sw10p: small-CFO study full SNR sweep, small_rx without (C) / with (D) checkpoints, paired seeds
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_sw10p.out
$PY -u blind_ber.py --points 1/10:-6:8 1/10:-5.5:8 1/10:-4.5:8 --max-frames 25000 --min-errors 100 --rx "S pilots N3x8, no checkpoints, MF per candidate, CA retry + CRC" "S pilots N3x8, checkpoints + CRC" --seed 5701 --part sw10p0 >> logs/run_sw10p.out 2>&1
$PY -u blind_ber.py --points 1/10:-3:8 1/10:-2:8 1/10:-1:8 1/10:0:8 --max-frames 50000 --min-errors 100 --rx "S pilots N3x8, no checkpoints, MF per candidate, CA retry + CRC" "S pilots N3x8, checkpoints + CRC" --seed 5701 --part sw10p1 >> logs/run_sw10p.out 2>&1
