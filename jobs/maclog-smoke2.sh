#!/bin/bash
# maclog-smoke2: rerun of the two blind logging arms after the genie KeyError fix (blind_ber.py:764); compare with the opt-out parts a0/b0 of maclog-smoke. Original header: per-packet MACs log smoke (small_rx mac_acc / blind_ber macs_*.npz, est4/run_bler.py macs_*.npz; read by
# BLIND_IMPLEMENTATION/testing/cap_post.py), 2026-11-15:
#   a / b  = testing_s11g R 0.15 -4 dB / base25_qfix R 2/5 0.5 dB, 2 chunks x 300 packets (3 batches per file), seed 8051
#   c      = est4 R 0.15 -4 dB, 1600 packets in 4 chunks, pn 0, seed 81: RCS2-13, pre128 ML (est4 branch), VDE-SAT, hyb3
#            (est5 branch), RCS2-13 lobes, Griebel faithful (ARS branch)
#   a0 / b0 / c0 = the same with the log switched off (BLIND_NO_MACLOG=1 / EST4_NO_MACLOG=1), same seeds: same packets
# PASS criteria (b)-(f) automatic: py BLIND_IMPLEMENTATION/testing/maclog_check.py (after syncing the parts' results,
# small_cfo/blind/dumps/t-maclog-smoke-{a,b}, est4/dumps/maclog-smoke-c and this log):
#   (a) 6 "EVAL DONE" lines, "ALL DONE", no Traceback in logs/run_maclog-smoke.out
#   (b) one npz per (chunk, rx) for blind, one per (part, chunk) for est4 (with every source); none in a0 / b0 / c0
#   (c) cap_post.py --parts "*maclog-smoke*": MATCH on every check row
#   (d) no NaN / inf per-packet cost (blind) or coef (est4); no "WARNING maclog" line in the log
#   (e) logging vs opt-out JSONs identical except time / timed_frames / time_est / us_est_per_frame
#   (f) pkt contiguous 0 .. n - 1 (blind pkt; est4 pkt0 = 0, contiguous batches, n summing to the JSON frames)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results est4/logs est4/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( BLIND_STUDY=small_cfo $R --max-frames 300 --seed 8051 --points 0.15:-4:2 --rx testing_s11g --part t-maclog-smoke-a
  BLIND_STUDY=small_cfo $R --max-frames 300 --seed 8051 --points 2/5:0.5:2 --rx base25_qfix --part t-maclog-smoke-b
  echo "ALL DONE" ) > logs/run_maclog-smoke2.out 2>&1
