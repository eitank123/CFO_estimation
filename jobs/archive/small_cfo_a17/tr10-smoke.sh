#!/bin/bash
# tr10-smoke: blind R = 1/10 trading BLER margin for MACs (2 phases / hard cut at 1/2 / both) on the coarse-start
# receiver with the tree cost, short paired runs at -5, -4.5, -4 dB against the same receiver unchanged
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_tr10-smoke.out
C="S blind, checkpoints, coarse start"
$PY -u blind_ber.py --points 1/10:-5:16 1/10:-4.5:16 1/10:-4:16 --max-frames 200 --min-errors 100 --rx "$C, rescue, tree cost + CRC" "$C, 2 phases, rescue, tree cost + CRC" "$C, hard cut, rescue, tree cost + CRC" "$C, 2 phases, hard cut, rescue, tree cost + CRC" --seed 5701 --part smoke-tr10 >> logs/run_tr10-smoke.out 2>&1
echo "SMOKE DONE" >> logs/run_tr10-smoke.out
