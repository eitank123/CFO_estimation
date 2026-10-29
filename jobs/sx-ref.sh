#!/bin/bash
# sx-ref: small-CFO study (|f| <= 0.03): the +-0.2 final receivers (with spectral / cyclic statistics) for reference
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_sx-ref.out
$PY -u blind_ber.py --points 1/10:-5:8 --max-frames 25000 --min-errors 100 --rx "Pilots N3x8 + v3 eco7, rescue, rho_n + CRC" "v3 eco7, rescue, rho_n + CRC" --seed 5701 --part sx-ref0 >> logs/run_sx-ref.out 2>&1
$PY -u blind_ber.py --points 2/5:0.5:8 2/5:1:8 --max-frames 50000 --min-errors 100 --rx "Pilots N3x8 + v3 eco7, rescue, rho_n + CRC" "v3 eco7, rescue, rho_n + CRC" --seed 5702 --part sx-ref1 >> logs/run_sx-ref.out 2>&1
$PY -u blind_ber.py --points 1/2:2:8 --max-frames 50000 --min-errors 100 --rx "Pilots N3x8 + v3 eco7, rescue, rho_n + CRC" "v3 eco7, rescue, rho_n + CRC" --seed 5703 --part sx-ref2 >> logs/run_sx-ref.out 2>&1
