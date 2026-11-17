#!/bin/bash
# v-smoke2: re-smoke after the SCAN clip fix in est4/run_bler.py hyp_matrix (2026-11-15). s15 / h15 repeat the v-smoke
# parts with the same seeds (paired: only packets with |f_hat| > MAX_CFO may change; expect SOF26 in_search 1.0);
# s10 = SOF26 stress point at 1/10 -5 dB (new seed 178).
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs est4/logs est4/results
( $PY -u est4/run_bler.py --rate 0.15 --snrs -4 --frames 800 --min-err 100000 --chunks 8 --seed 135 --pn 0 --sources "DVB-S2 style" "DVB-S2 SOF26" --part v-smoke2-s15
  $PY -u est4/run_bler.py --rate 0.15 --snrs -4 --frames 800 --min-err 100000 --chunks 8 --seed 132 --pn 0 --sources "DVB-S2 style" "DVB-S2 header90" --part v-smoke2-h15
  $PY -u est4/run_bler.py --rate 1/10 --snrs -5 --frames 800 --min-err 100000 --chunks 8 --seed 178 --pn 0 --sources "DVB-S2 style" "DVB-S2 SOF26" --part v-smoke2-s10
  echo "ALL DONE" ) > logs/run_v-smoke2.out 2>&1
