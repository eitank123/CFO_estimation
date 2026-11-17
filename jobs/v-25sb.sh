#!/bin/bash
# v-25sb: R = 2/5, pn 0, 240k at 0 dB in chunks of 4000 (half; other half v-25sa, own seed), SNRs 0 (re-split of v-25s after v-smoke, 2026-11-15): DVB-S2 SOF26 + parent DVB-S2 style
# (faithful variants of the est5 competitors, expected_variants.md, 2026-11-15; each variant McNemar-paired with its parent;
# header90 / SOF26 scan k STEP over the whole +-0.03, ~801 hypotheses per packet at every SNR)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs est4/logs est4/results
( $PY -u est4/run_bler.py --rate 2/5 --snrs 0 --frames 240000 --min-err 100000 --chunks 60 --seed 167 --pn 0 --sources "DVB-S2 style" "DVB-S2 SOF26" --part v-25sb
  echo "ALL DONE" ) > logs/run_v-25sb.out 2>&1
