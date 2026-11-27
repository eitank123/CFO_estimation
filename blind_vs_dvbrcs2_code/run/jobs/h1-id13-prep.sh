#!/bin/bash
# h1-id13-prep (2026-11-25, H1 step 1 ID 13, LS term of arms C / E): sync_cfo/fs/dual_lowweight.py --export-w4 id13:twc -> the explicit
# weight-4 checks of the moved-bit twc code (search:k18:rd, CRC-24; dual_lowweight.md: 445 weight-4 words, 444 on 4 distinct symbols)
# in data/dual_w4_id13_twc.json (the small_rx h1 "ls" / pk_w4 json); code structure only, no packets; NO rpz.
# Run BEFORE h1-id13-smoke / -pk-m06 and every C / E job (C0 and A do not need it); est. wall time ~1-3 min; disk < 1 MB
cd "$(dirname "$(readlink -f "$0")")/.."
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo BLIND_MAC_UNIT=ops
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs data
( date
  $PY -u dual_lowweight.py --export-w4 id13:twc
  test -s data/dual_w4_id13_twc.json || { echo "FAILED: dual_w4_id13_twc.json missing"; exit 2; }
  date
  echo "ALL DONE" ) > logs/run_h1-id13-prep.out 2>&1
