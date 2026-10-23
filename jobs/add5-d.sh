#!/bin/bash
# add5-d: extra frames ("add5" parts, own seeds): split pilots (quarter) full search / first pass, NN v2 full search; 16 single-core lanes, chunks in sequence.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_add5-d.out
PROG=logs/add5-d.progress
TOTAL=35
T0=$(date +%s)
mkdir -p logs lowrate/logs
: > "$PROG"
echo "$(date "+%F %T") start, $TOTAL chunks" > "$LOG"
finish() {  # name status
  echo "$(date "+%F %T") $2 $1" >> "$LOG"
  until mkdir "$PROG.lock" 2>/dev/null; do sleep 1; done
  echo $(( $(wc -l < "$PROG") + 1 )) $TOTAL $(( $(date +%s) - T0 )) >> "$PROG"
  rmdir "$PROG.lock"
}
run() {  # tag packet code source esn0 frames seed
  if $PY -u polar_ber_experiment.py --mode ebn0 --packet $2 --codes "$3" --sources "$4" --tag $1 --extra-esn0 $5 --min-errors 1000000 --max-frames $6 --seed $7 --workers 1 > lowrate/logs/run_$1.out 2>&1; then finish $1 DONE; else finish $1 "FAILED (exit $?)"; fi
}
( run add5-p512c16-sqfull-0-13 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" 0 3429000 5206; run add5-p1024c16-v2full-0-4 1024 "R=0.1,C16" "NN v2 + CRC search" 0 587000 5304; run add5-p512c11-sqfull-m2p5-0 512 "R=0.1" "Split pilots, quarter (ML) + CRC search" -2.5 1187500 5006 ) &   # ~2.7 h
( run add5-p512c16-sqf-m3-0 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -3 3250000 5035; run add5-p512c16-v2full-m2-6 512 "R=0.1,C16" "NN v2 + CRC search" -2 2411000 5088 ) &   # ~2.2 h
( run add5-p512c16-sqf-m1p5-0 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -1.5 3423500 5090; run add5-p1024c16-v2full-m1p5-3 1024 "R=0.1,C16" "NN v2 + CRC search" -1.5 257000 5272 ) &   # ~2.2 h
( run add5-p512c16-sqf-m1p5-1 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -1.5 3423500 5091; run add5-p1024c16-v2full-m1p5-4 1024 "R=0.1,C16" "NN v2 + CRC search" -1.5 257000 5273 ) &   # ~2.2 h
( run add5-p512c16-sqf-m1p5-2 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -1.5 3423500 5092; run add5-p512c16-sqfull-m2p5-0 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -2.5 2143000 5044 ) &   # ~2.2 h
( run add5-p512c16-sqf-m1p5-3 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -1.5 3423500 5093; run add5-p512c16-sqfull-m2p5-1 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -2.5 2143000 5045 ) &   # ~2.2 h
( run add5-p512c16-sqf-m1p5-4 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -1.5 3423500 5094; run add5-p512c16-sqfull-m2p5-2 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -2.5 2143000 5046 ) &   # ~2.2 h
( run add5-p512c16-sqf-m1p5-5 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -1.5 3423500 5095; run add5-p512c16-sqfull-m2p5-3 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -2.5 2143000 5047 ) &   # ~2.2 h
( run add5-p512c16-sqf-m1p5-6 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -1.5 3423500 5096; run add5-p512c16-sqfull-m2p5-4 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -2.5 2143000 5048 ) &   # ~2.2 h
( run add5-p512c16-sqf-m1p5-7 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -1.5 3423500 5097; run add5-p512c16-v2full-m2-0 512 "R=0.1,C16" "NN v2 + CRC search" -2 2411000 5082; run add5-p512c11-sqfull-m5-0 512 "R=0.1" "Split pilots, quarter (ML) + CRC search" -5 23500 5000 ) &   # ~2.2 h
( run add5-p512c16-sqf-m1p5-8 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -1.5 3423500 5098; run add5-p512c16-v2full-m2-1 512 "R=0.1,C16" "NN v2 + CRC search" -2 2411000 5083; run add5-p512c16-sqfull-m5-0 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -5 11500 5028 ) &   # ~2.2 h
( run add5-p512c16-sqf-m1p5-9 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -1.5 3423500 5099; run add5-p512c16-v2full-m2-2 512 "R=0.1,C16" "NN v2 + CRC search" -2 2411000 5084 ) &   # ~2.2 h
( run add5-p512c16-sqf-m1p5-10 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -1.5 3423500 5100; run add5-p512c16-v2full-m2-3 512 "R=0.1,C16" "NN v2 + CRC search" -2 2411000 5085 ) &   # ~2.2 h
( run add5-p512c16-sqf-m1p5-11 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -1.5 3423500 5101; run add5-p512c16-v2full-m2-4 512 "R=0.1,C16" "NN v2 + CRC search" -2 2411000 5086 ) &   # ~2.2 h
( run add5-p512c16-sqf-m1p5-12 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -1.5 3423500 5102; run add5-p512c16-v2full-m2-5 512 "R=0.1,C16" "NN v2 + CRC search" -2 2411000 5087 ) &   # ~2.2 h
( run add5-p512c16-sqfull-m1p5-0 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1.5 3000000 5103; run add5-p1024c16-v2full-m4p5-0 1024 "R=0.1,C16" "NN v2 + CRC search" -4.5 68000 5210 ) &   # ~2.2 h
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
