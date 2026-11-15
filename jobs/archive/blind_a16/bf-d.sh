#!/bin/bash
# bf-d: blind best-first search (blind_fast.py), BLER + wall time, points 1/10:-5:4 1/10:-3:4 1/10:-1:4 1/10:0:4
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results
$PY -u blind_ber.py --points 1/10:-5:4 1/10:-3:4 1/10:-1:4 1/10:0:4 --max-frames 15000 --min-errors 100 --rx "Best-first search (spectral only) + CRC" "Best-first search (spectral + cyclic + 4th) + CRC" "Best-first search, z0 = 3 + CRC" "Best-first search, z0 = 5 + CRC" "Best-first search, exact box-plus + CRC" --seed 5104 --part bf-d > logs/run_bf-d.out 2>&1
