#!/bin/bash
# add3-f: extra frames ("add3" parts, own seeds) for jittery BLER points; 16 single-core lanes, chunks in sequence.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_add3-f.out
PROG=logs/add3-f.progress
TOTAL=16
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

( run add3-p512c16-v2f-0-0 512 "R=0.1,C16" "NN v2 + CRC search (first pass)" 0 3429000 3097 ) &   # ~1.1 h
( run add3-p512c16-v2f-0-1 512 "R=0.1,C16" "NN v2 + CRC search (first pass)" 0 3429000 3098 ) &   # ~1.1 h
( run add3-p512c16-v2f-0-2 512 "R=0.1,C16" "NN v2 + CRC search (first pass)" 0 3429000 3099 ) &   # ~1.1 h
( run add3-p512c16-v2f-0-3 512 "R=0.1,C16" "NN v2 + CRC search (first pass)" 0 3429000 3100 ) &   # ~1.1 h
( run add3-p512c16-v2f-0-4 512 "R=0.1,C16" "NN v2 + CRC search (first pass)" 0 3429000 3101 ) &   # ~1.1 h
( run add3-p512c16-v2f-0-5 512 "R=0.1,C16" "NN v2 + CRC search (first pass)" 0 3429000 3102 ) &   # ~1.1 h
( run add3-p512c16-v2f-0-6 512 "R=0.1,C16" "NN v2 + CRC search (first pass)" 0 3429000 3103 ) &   # ~1.1 h
( run add3-p512c16-v2f-0-7 512 "R=0.1,C16" "NN v2 + CRC search (first pass)" 0 3429000 3104 ) &   # ~1.1 h
( run add3-p512c16-v2f-0-8 512 "R=0.1,C16" "NN v2 + CRC search (first pass)" 0 3429000 3105 ) &   # ~1.1 h
( run add3-p512c16-v2f-0-9 512 "R=0.1,C16" "NN v2 + CRC search (first pass)" 0 3429000 3106 ) &   # ~1.1 h
( run add3-p512c16-v2f-0-10 512 "R=0.1,C16" "NN v2 + CRC search (first pass)" 0 3429000 3107 ) &   # ~1.1 h
( run add3-p512c16-v2f-0-11 512 "R=0.1,C16" "NN v2 + CRC search (first pass)" 0 3429000 3108 ) &   # ~1.1 h
( run add3-p512c16-v2f-0-12 512 "R=0.1,C16" "NN v2 + CRC search (first pass)" 0 3429000 3109 ) &   # ~1.1 h
( run add3-p512c16-v2f-0-13 512 "R=0.1,C16" "NN v2 + CRC search (first pass)" 0 3429000 3110 ) &   # ~1.1 h
( run add3-p512c16-v2f-m1-0 512 "R=0.1,C16" "NN v2 + CRC search (first pass)" -1 3375000 3123 ) &   # ~1.1 h
( run add3-p512c16-v2f-m1-1 512 "R=0.1,C16" "NN v2 + CRC search (first pass)" -1 3375000 3124 ) &   # ~1.1 h
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
