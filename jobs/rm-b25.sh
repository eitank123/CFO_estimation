#!/bin/bash
# rm-b25: blind rescue mid (128 posterior cells) + rho_n at the R = 2/5 waterfall and R = 1/2 2 dB (paired with rh-b25/b2)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 2/5:0.5:8 2/5:1:8 --max-frames 50000 --min-errors 100 --rx "v3 eco7, rescue mid, rho_n + CRC" --seed 5702 --part rm-b25 > logs/run_rm-b25.out 2>&1
$PY -u blind_ber.py --points 1/2:2:8 --max-frames 50000 --min-errors 100 --rx "v3 eco7, rescue mid, rho_n + CRC" --seed 5703 --part rm-b2 > logs/run_rm-b2.out 2>&1
