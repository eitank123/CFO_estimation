#!/bin/bash
# nn-r25a: NN peak grader in the fast path, blind R = 2/5 (paired with eco6/eco7)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results blind/models
$PY -u blind_ber.py --points 2/5:0.5:8 2/5:1:8 2/5:1.5:8 2/5:2:8 2/5:2.5:8 2/5:3:8 2/5:4:8 --max-frames 50000 --min-errors 100 --rx "v3 eco7, NN peak + CRC" "v3 eco7, NN peak, skip 0.8 + CRC" --seed 5702 --part nn-r25a > logs/run_nn-r25a.out 2>&1
