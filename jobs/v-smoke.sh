#!/bin/bash
# v-smoke: faithful variants of the est5 competitors (expected_variants.md, 2026-11-15), every variant + its parent, 800 packets
# at the high-BLER points R 0.15 -4 dB (parts *15) and R 2/5 0.5 dB (parts *25), pn 0; one part per full-job group
# (m = v-r, h = v-rh, p = v-rp, w = v-rw, s = v-rs) so each part time sizes its job; Genie in the m parts.
# v-smoke-id: e5-smoke-a repeated exactly (same seed 61, rate, SNR, frames, chunks, sources, arguments): the est5
# sources must reproduce bler_e5-smoke-a.json exactly (identity check of the variant edits)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs est4/logs est4/results
( $PY -u est4/run_bler.py --rate 0.15 --snrs -4 --frames 800 --min-err 100000 --chunks 8 --seed 61 --pn 0 --sources Genie "VDE-SAT" "DVB-S2 style" "CCSDS style" "DMRS 1/7" "Sparse pilots 1/32" "WiFi pre128" "MIL-110 HF" "ViaSat UW" "hyb3" "CCSDS style blocks" --part v-smoke-id
  $PY -u est4/run_bler.py --rate 0.15 --snrs -4 --frames 800 --min-err 100000 --chunks 8 --seed 131 --pn 0 --sources Genie "MIL-110 HF" "MIL-110 full" "split64 ML" "split64 ML L4" "CCSDS 131.0 ASM" "CCSDS style" "CCSDS 131.2 real" --part v-smoke-m15
  $PY -u est4/run_bler.py --rate 0.15 --snrs -4 --frames 800 --min-err 100000 --chunks 8 --seed 132 --pn 0 --sources "DVB-S2 style" "DVB-S2 header90" --part v-smoke-h15
  $PY -u est4/run_bler.py --rate 0.15 --snrs -4 --frames 800 --min-err 100000 --chunks 8 --seed 133 --pn 0 --sources "ViaSat UW" "ViaSat 7653150" "ViaSat top32 X4phase" "hyb3" "hyb3-pre48" "hyb3-pre48 wide" --part v-smoke-p15
  $PY -u est4/run_bler.py --rate 0.15 --snrs -4 --frames 800 --min-err 100000 --chunks 8 --seed 134 --pn 0 --sources "WiFi pre128" "WiFi real320" "WiFi real320 lobes" --part v-smoke-w15
  $PY -u est4/run_bler.py --rate 0.15 --snrs -4 --frames 800 --min-err 100000 --chunks 8 --seed 135 --pn 0 --sources "DVB-S2 style" "DVB-S2 SOF26" --part v-smoke-s15
  $PY -u est4/run_bler.py --rate 2/5 --snrs 0.5 --frames 800 --min-err 100000 --chunks 8 --seed 131 --pn 0 --sources Genie "MIL-110 HF" "MIL-110 full" "split64 ML" "split64 ML L4" "CCSDS 131.0 ASM" "CCSDS style" "CCSDS 131.2 real" --part v-smoke-m25
  $PY -u est4/run_bler.py --rate 2/5 --snrs 0.5 --frames 800 --min-err 100000 --chunks 8 --seed 132 --pn 0 --sources "DVB-S2 style" "DVB-S2 header90" --part v-smoke-h25
  $PY -u est4/run_bler.py --rate 2/5 --snrs 0.5 --frames 800 --min-err 100000 --chunks 8 --seed 133 --pn 0 --sources "ViaSat UW" "ViaSat 7653150" "ViaSat top32 X4phase" "hyb3" "hyb3-pre48" "hyb3-pre48 wide" --part v-smoke-p25
  $PY -u est4/run_bler.py --rate 2/5 --snrs 0.5 --frames 800 --min-err 100000 --chunks 8 --seed 134 --pn 0 --sources "WiFi pre128" "WiFi real320" "WiFi real320 lobes" --part v-smoke-w25
  $PY -u est4/run_bler.py --rate 2/5 --snrs 0.5 --frames 800 --min-err 100000 --chunks 8 --seed 135 --pn 0 --sources "DVB-S2 style" "DVB-S2 SOF26" --part v-smoke-s25
  echo "ALL DONE" ) > logs/run_v-smoke.out 2>&1
