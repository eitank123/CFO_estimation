#!/bin/bash
# add3-h: extra frames ("add3" parts, own seeds) for jittery BLER points; 16 single-core lanes, chunks in sequence.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_add3-h.out
PROG=logs/add3-h.progress
TOTAL=29
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

( run add3-p512c16-nnfull-m1-1 512 "R=0.1,C16" "SNR-aware NN + CRC search" -1 3030000 3025 ) &   # ~1.0 h
( run add3-p512c16-nnfull-m1-2 512 "R=0.1,C16" "SNR-aware NN + CRC search" -1 3030000 3026 ) &   # ~1.0 h
( run add3-p512c16-nnfull-m1-3 512 "R=0.1,C16" "SNR-aware NN + CRC search" -1 3030000 3027 ) &   # ~1.0 h
( run add3-p512c16-v2f-m1p5-0 512 "R=0.1,C16" "NN v2 + CRC search (first pass)" -1.5 3000000 3131; run add3-p1024c16-nnfull-m1p5-0 1024 "R=0.1,C16" "SNR-aware NN + CRC search" -1.5 365000 3141 ) &   # ~1.2 h
( run add3-p512c16-v2f-m1p5-1 512 "R=0.1,C16" "NN v2 + CRC search (first pass)" -1.5 3000000 3132; run add3-p1024c16-nnfull-m1-0 1024 "R=0.1,C16" "SNR-aware NN + CRC search" -1 339000 3140 ) &   # ~1.1 h
( run add3-p512c16-v2f-m1p5-2 512 "R=0.1,C16" "NN v2 + CRC search (first pass)" -1.5 3000000 3133; run add3-p512c11-mmf-m0p5-0 512 "R=0.1" "M&M + CRC search (first pass)" -0.5 462000 3035 ) &   # ~1.1 h
( run add3-p512c16-v2f-m1p5-3 512 "R=0.1,C16" "NN v2 + CRC search (first pass)" -1.5 3000000 3134; run add3-p512c11-nnf-m1-0 512 "R=0.1" "SNR-aware NN + CRC search (first pass)" -1 343000 3029 ) &   # ~1.1 h
( run add3-p512c16-v2f-m1p5-4 512 "R=0.1,C16" "NN v2 + CRC search (first pass)" -1.5 3000000 3135; run add3-p512c16-v2f-m2p5-0 512 "R=0.1,C16" "NN v2 + CRC search (first pass)" -2.5 214500 3137 ) &   # ~1.0 h
( run add3-p512c11-nnf-0-0 512 "R=0.1" "SNR-aware NN + CRC search (first pass)" 0 2700000 3030; run add3-p1024c16-nnfull-0-0 1024 "R=0.1,C16" "SNR-aware NN + CRC search" 0 536000 3138 ) &   # ~1.1 h
( run add3-p512c11-mmf-0-0 512 "R=0.1" "M&M + CRC search (first pass)" 0 2591000 3033; run add3-p512c16-v2f-m2-0 512 "R=0.1,C16" "NN v2 + CRC search (first pass)" -2 1500000 3136 ) &   # ~1.3 h
( run add3-p512c11-mmf-0-1 512 "R=0.1" "M&M + CRC search (first pass)" 0 2591000 3034; run add3-p512c16-nnf-m1p5-0 512 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" -1.5 1286000 3096 ) &   # ~1.3 h
( run add3-p512c11-nnfull-0-0 512 "R=0.1" "SNR-aware NN + CRC search" 0 2476000 3000; run add3-p1024c16-nnfull-m0p5-0 1024 "R=0.1,C16" "SNR-aware NN + CRC search" -0.5 1295000 3139 ) &   # ~1.4 h
( run add3-p512c11-nnfull-0-1 512 "R=0.1" "SNR-aware NN + CRC search" 0 2476000 3001; run add3-p512c11-nnf-m0p5-0 512 "R=0.1" "SNR-aware NN + CRC search (first pass)" -0.5 1950000 3031 ) &   # ~1.4 h
( run add3-p512c11-nnfull-0-2 512 "R=0.1" "SNR-aware NN + CRC search" 0 2476000 3002; run add3-p512c11-v2f-m0p5-0 512 "R=0.1" "NN v2 + CRC search (first pass)" -0.5 1737000 3036 ) &   # ~1.4 h
( run add3-p512c16-nnfull-m1p5-0 512 "R=0.1,C16" "SNR-aware NN + CRC search" -1.5 2317500 3028; run add3-p512c11-nnfull-m0p5-0 512 "R=0.1" "SNR-aware NN + CRC search" -0.5 2150000 3003 ) &   # ~1.4 h
( run add3-p512c16-nnf-m1-0 512 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" -1 2250000 3094; run add3-p512c16-nnf-m1-1 512 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" -1 2250000 3095 ) &   # ~1.5 h
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
