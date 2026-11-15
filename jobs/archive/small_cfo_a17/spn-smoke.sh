#!/bin/bash
# spn-smoke: smoke test of the cell-prior NN (small_prior_nn.py: tiny train + eval, both modes), of the NN receivers,
# and a regression check of the restructured small_rx search loop (same chunks as sm-s5: decodes must match)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results small_cfo/blind/models
: > logs/run_spn-smoke.out
$PY -u blind_ber.py --points 1/10:-5:8 2/5:0.5:8 --max-frames 150 --min-errors 100 --rx "S blind, checkpoints, coarse start, rescue + CRC" "S pilots N3x8, checkpoints, pilot score, rescue + CRC" --seed 5701 --part smoke-reg >> logs/run_spn-smoke.out 2>&1
for m in blind pilots; do
  $PY -u small_prior_nn.py train --mode $m --epochs 2 --steps 5 --val 100 --producers 8 >> logs/run_spn-smoke.out 2>&1
  $PY -u small_prior_nn.py eval --mode $m --frames 200 >> logs/run_spn-smoke.out 2>&1
done
$PY -u blind_ber.py --points 1/10:-5:4 2/5:0.5:4 --max-frames 100 --min-errors 100 --rx "S blind, no checkpoints, MF per candidate, CA retry, NN shortlist + score, rescue + CRC" "S blind, checkpoints, coarse start, NN shortlist, rescue + CRC" "S pilots N3x8, checkpoints, pilot score, NN shortlist + score, rescue + CRC" --seed 5701 --part smoke-nn >> logs/run_spn-smoke.out 2>&1
echo "SMOKE DONE" >> logs/run_spn-smoke.out
