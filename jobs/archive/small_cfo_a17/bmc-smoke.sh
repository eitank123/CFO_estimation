#!/bin/bash
# bmc-smoke: blind MAC cuts with the existing methods (best-first by the 4th-power periodogram, 4-peak fast path,
# coarse start + PM beam), tree cost, short paired runs: R = 2/5 0.5 / 1 dB, R = 1/10 -5 dB
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
: > logs/run_bmc-smoke.out
N="S blind, checkpoints, checkpoint NN"; C="S blind, checkpoints, coarse start"
$PY -u blind_ber.py --points 2/5:0.5:16 2/5:1:16 --max-frames 100 --min-errors 100 --rx "$N, rescue, tree cost + CRC" "$N, best-first 32, rescue, tree cost + CRC" "$N, 4-peak fast path, rescue, tree cost + CRC" "$N, best-first 32, 4-peak fast path, rescue, tree cost + CRC" --seed 5702 --part smoke-bmc25 >> logs/run_bmc-smoke.out 2>&1
$PY -u blind_ber.py --points 1/10:-5:16 --max-frames 100 --min-errors 100 --rx "$C, rescue, tree cost + CRC" "$C, beam, rescue, tree cost + CRC" --seed 5701 --part smoke-bmc10 >> logs/run_bmc-smoke.out 2>&1
echo "SMOKE DONE" >> logs/run_bmc-smoke.out
