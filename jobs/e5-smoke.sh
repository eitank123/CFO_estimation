#!/bin/bash
# e5-smoke: est5 deployed preamble / pilot competitors (expected_est5.md, 2026-11-15), all new sources + Genie, 800 packets:
# a = R 0.15 per-symbol -4 dB, b = R 2/5 0.5 dB (pn 0); c = R 0.15 -4 dB pn 1e-4, the track variants (Kalman path, extended
# phase-noise path for dmrs7 / mil110)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs est4/logs est4/results
( $PY -u est4/run_bler.py --rate 0.15 --snrs -4 --frames 800 --min-err 100000 --chunks 8 --seed 61 --pn 0 --sources Genie "VDE-SAT" "DVB-S2 style" "CCSDS style" "DMRS 1/7" "Sparse pilots 1/32" "WiFi pre128" "MIL-110 HF" "ViaSat UW" "hyb3" "CCSDS style blocks" --part e5-smoke-a
  $PY -u est4/run_bler.py --rate 2/5 --snrs 0.5 --frames 800 --min-err 100000 --chunks 8 --seed 61 --pn 0 --sources Genie "VDE-SAT" "DVB-S2 style" "CCSDS style" "DMRS 1/7" "Sparse pilots 1/32" "WiFi pre128" "MIL-110 HF" "ViaSat UW" "hyb3" "CCSDS style blocks" --part e5-smoke-b
  $PY -u est4/run_bler.py --rate 0.15 --snrs -4 --frames 800 --min-err 100000 --chunks 8 --seed 61 --pn 1e-4 --sources Genie "VDE-SAT track" "CCSDS style track" "DMRS 1/7 track" "MIL-110 HF track" "VDE-SAT" --part e5-smoke-c
  echo "ALL DONE" ) > logs/run_e5-smoke.out 2>&1
