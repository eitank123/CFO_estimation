#!/bin/bash
# pmr-smoke: PM racing in the receiver (beam at R = 1/10, phase racing at 2/5, 1/2) + the Fast-SSC tree cost, short
# runs against the same receivers re-counted with the tree cost (blind checkpoints + rescue, pilots H + rescue)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_pmr-smoke.out
B="S blind, checkpoints"; P="S pilots N3x8, checkpoints, pilot score"
RXS=("$B, rescue + CRC" "$B, rescue, tree cost + CRC" "$B, PM racing, rescue, tree cost + CRC" "$P, rescue + CRC" "$P, rescue, tree cost + CRC" "$P, PM racing, rescue, tree cost + CRC")
$PY -u blind_ber.py --points 1/10:-5:16 --max-frames 100 --min-errors 100 --rx "${RXS[@]}" --seed 5701 --part smoke-pmr10 >> logs/run_pmr-smoke.out 2>&1
$PY -u blind_ber.py --points 2/5:0.5:16 --max-frames 100 --min-errors 100 --rx "${RXS[@]}" --seed 5702 --part smoke-pmr25 >> logs/run_pmr-smoke.out 2>&1
$PY -u blind_ber.py --points 1/2:2:16 --max-frames 100 --min-errors 100 --rx "${RXS[@]}" --seed 5703 --part smoke-pmr2 >> logs/run_pmr-smoke.out 2>&1
echo "SMOKE DONE" >> logs/run_pmr-smoke.out
