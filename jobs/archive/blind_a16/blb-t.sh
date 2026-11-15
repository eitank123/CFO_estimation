#!/bin/bash
# blb-t: wall time per packet of the earlier blind receivers (one receiver per run: no shared candidate refinement), 1000 frames per point
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs blind/logs blind/results
: > logs/run_blb-t.out
$PY -u blind_ber.py --points 1/10:-2:1 1/10:0:1 1/10:2:1 1/10:4:1 1/4:0:1 1/4:1:1 1/4:2:1 1/4:3:1 1/4:4:1 1/4:6:1 1/4:8:1 1/4:10:1 1/2:2:1 1/2:3:1 1/2:4:1 1/2:6:1 1/2:8:1 1/2:10:1 --max-frames 1000 --min-errors 1000000000 --rx "4th power + CRC (phase mod pi)" --seed 4201 --part t1 >> logs/run_blb-t.out 2>&1
$PY -u blind_ber.py --points 1/10:-2:1 1/10:0:1 1/10:2:1 1/10:4:1 1/4:0:1 1/4:1:1 1/4:2:1 1/4:3:1 1/4:4:1 1/4:6:1 1/4:8:1 1/4:10:1 1/2:2:1 1/2:3:1 1/2:4:1 1/2:6:1 1/2:8:1 1/2:10:1 --max-frames 1000 --min-errors 1000000000 --rx "4th power + SC search + CRC" --seed 4202 --part t2 >> logs/run_blb-t.out 2>&1
$PY -u blind_ber.py --points 1/10:-2:1 1/10:0:1 1/10:2:1 1/10:4:1 1/4:0:1 1/4:1:1 1/4:2:1 1/4:3:1 1/4:4:1 1/4:6:1 1/4:8:1 1/4:10:1 1/2:2:1 1/2:3:1 1/2:4:1 1/2:6:1 1/2:8:1 1/2:10:1 --max-frames 1000 --min-errors 1000000000 --rx "4th power + turbo (DD) + CRC" --seed 4203 --part t3 >> logs/run_blb-t.out 2>&1
$PY -u blind_ber.py --points 1/10:-5:1 1/10:-4:1 1/10:-3:1 1/10:-2:1 1/10:-1:1 1/10:0:1 1/4:0:1 1/4:1:1 1/4:2:1 1/4:3:1 1/4:4:1 1/2:2:1 1/2:3:1 1/2:4:1 1/2:6:1 --max-frames 1000 --min-errors 1000000000 --rx "Spectral grid + SC search + CRC" --seed 4204 --part t4 >> logs/run_blb-t.out 2>&1
$PY -u blind_ber.py --points 1/10:-5:1 1/10:-4:1 1/10:-3:1 1/10:-2:1 1/10:-1:1 1/10:0:1 1/4:0:1 1/4:1:1 1/4:2:1 1/4:3:1 1/4:4:1 1/2:2:1 1/2:3:1 1/2:4:1 1/2:6:1 --max-frames 1000 --min-errors 1000000000 --rx "4th power + SC search, then spectral grid + CRC" --seed 4205 --part t5 >> logs/run_blb-t.out 2>&1
