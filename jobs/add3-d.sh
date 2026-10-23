#!/bin/bash
# add3-d: extra frames ("add3" parts, own seeds) for jittery BLER points; 16 single-core lanes, chunks in sequence.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_add3-d.out
PROG=logs/add3-d.progress
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

( run add3-p512c16-nnfull-0-10 512 "R=0.1,C16" "SNR-aware NN + CRC search" 0 3429000 3014 ) &   # ~1.1 h
( run add3-p512c16-nnfull-0-11 512 "R=0.1,C16" "SNR-aware NN + CRC search" 0 3429000 3015 ) &   # ~1.1 h
( run add3-p512c16-nnfull-0-12 512 "R=0.1,C16" "SNR-aware NN + CRC search" 0 3429000 3016 ) &   # ~1.1 h
( run add3-p512c16-nnfull-0-13 512 "R=0.1,C16" "SNR-aware NN + CRC search" 0 3429000 3017 ) &   # ~1.1 h
( run add3-p512c16-mmf-0-0 512 "R=0.1,C16" "M&M + CRC search (first pass)" 0 3429000 3039 ) &   # ~1.1 h
( run add3-p512c16-mmf-0-1 512 "R=0.1,C16" "M&M + CRC search (first pass)" 0 3429000 3040 ) &   # ~1.1 h
( run add3-p512c16-mmf-0-2 512 "R=0.1,C16" "M&M + CRC search (first pass)" 0 3429000 3041 ) &   # ~1.1 h
( run add3-p512c16-mmf-0-3 512 "R=0.1,C16" "M&M + CRC search (first pass)" 0 3429000 3042 ) &   # ~1.1 h
( run add3-p512c16-mmf-0-4 512 "R=0.1,C16" "M&M + CRC search (first pass)" 0 3429000 3043 ) &   # ~1.1 h
( run add3-p512c16-mmf-0-5 512 "R=0.1,C16" "M&M + CRC search (first pass)" 0 3429000 3044 ) &   # ~1.1 h
( run add3-p512c16-mmf-0-6 512 "R=0.1,C16" "M&M + CRC search (first pass)" 0 3429000 3045 ) &   # ~1.1 h
( run add3-p512c16-mmf-0-7 512 "R=0.1,C16" "M&M + CRC search (first pass)" 0 3429000 3046 ) &   # ~1.1 h
( run add3-p512c16-mmf-0-8 512 "R=0.1,C16" "M&M + CRC search (first pass)" 0 3429000 3047 ) &   # ~1.1 h
( run add3-p512c16-mmf-0-9 512 "R=0.1,C16" "M&M + CRC search (first pass)" 0 3429000 3048 ) &   # ~1.1 h
( run add3-p512c16-mmf-0-10 512 "R=0.1,C16" "M&M + CRC search (first pass)" 0 3429000 3049 ) &   # ~1.1 h
( run add3-p512c16-mmf-0-11 512 "R=0.1,C16" "M&M + CRC search (first pass)" 0 3429000 3050 ) &   # ~1.1 h
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
