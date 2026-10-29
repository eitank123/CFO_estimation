#!/bin/bash
# sm-s2: smoke of the small-CFO receiver variants (MF per candidate, CA retry, checkpoints, shortlist): runs + MACs
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
RX=()
for n in "S blind" "S pilots N3x8"; do for v in "no checkpoints, MF per candidate" "no checkpoints, MF per candidate, CA retry" "checkpoints" "checkpoints, shortlist"; do RX+=("$n, $v + CRC"); done; done
$PY -u blind_ber.py --points 1/10:-5:8 2/5:0.5:8 1/2:2:8 --max-frames 150 --min-errors 100 --rx "${RX[@]}" "Genie (known CFO, pre-MF correction)" --seed 5701 --part smoke-s2 > logs/run_sm-s2.out 2>&1
