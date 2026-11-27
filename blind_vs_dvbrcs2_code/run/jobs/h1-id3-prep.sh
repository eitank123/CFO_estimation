#!/bin/bash
# h1-id3-prep (2026-11-25, H1 / H2 step 1 ID 3, LS term of arms C / E / C2 / E2): OPTIONAL, only if the local json is
# not pushed: sync_cfo/fs/dual_lowweight.py --export-w4 id3:tz0 -> data/dual_w4_id3_tz0.json (108 weight-4 checks
# of the moved-bit tz0 code search:k18z0:rd, CRC-24); code structure only, no packets; NO rpz. est. wall ~1 min; disk < 1 MB
cd "$(dirname "$(readlink -f "$0")")/.."
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo BLIND_MAC_UNIT=ops
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs data
( date
  test ! -s data/dual_w4_id3_tz0.json || { echo "json present: kept (not rebuilt)"; echo "ALL DONE"; exit 0; }
  $PY -u dual_lowweight.py --export-w4 id3:tz0
  test -s data/dual_w4_id3_tz0.json || { echo "FAILED: dual_w4_id3_tz0.json missing"; exit 2; }
  date
  echo "ALL DONE" ) > logs/run_h1-id3-prep.out 2>&1
