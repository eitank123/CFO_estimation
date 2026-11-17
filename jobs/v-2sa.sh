#!/bin/bash
# v-2sa: R = 1/2, pn 0, 240k at 1.5 dB in chunks of 4000 (half; other half v-2sb, own seed), SNRs 1.5 (re-split of v-2s after v-smoke, 2026-11-15): DVB-S2 SOF26 + parent DVB-S2 style
# (faithful variants of the est5 competitors, expected_variants.md, 2026-11-15; each variant McNemar-paired with its parent;
# header90 / SOF26 scan k STEP over the whole +-0.03, ~801 hypotheses per packet at every SNR)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs est4/logs est4/results
( $PY -u est4/run_bler.py --rate 1/2 --snrs 1.5 --frames 240000 --min-err 100000 --chunks 60 --seed 175 --pn 0 --sources "DVB-S2 style" "DVB-S2 SOF26" --part v-2sa
  echo "ALL DONE" ) > logs/run_v-2sa.out 2>&1
