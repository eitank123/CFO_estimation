#!/bin/bash
# add3-b: extra frames ("add3" parts, own seeds) for jittery BLER points; 16 single-core lanes, chunks in sequence.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_add3-b.out
PROG=logs/add3-b.progress
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

( run add3-p512c16-nnf-m0p5-2 512 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" -0.5 3500000 3084 ) &   # ~1.1 h
( run add3-p512c16-nnf-m0p5-3 512 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" -0.5 3500000 3085 ) &   # ~1.1 h
( run add3-p512c16-nnf-m0p5-4 512 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" -0.5 3500000 3086 ) &   # ~1.1 h
( run add3-p512c16-nnf-m0p5-5 512 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" -0.5 3500000 3087 ) &   # ~1.1 h
( run add3-p512c16-nnf-m0p5-6 512 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" -0.5 3500000 3088 ) &   # ~1.1 h
( run add3-p512c16-nnf-m0p5-7 512 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" -0.5 3500000 3089 ) &   # ~1.1 h
( run add3-p512c16-nnf-m0p5-8 512 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" -0.5 3500000 3090 ) &   # ~1.1 h
( run add3-p512c16-nnf-m0p5-9 512 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" -0.5 3500000 3091 ) &   # ~1.1 h
( run add3-p512c16-nnf-m0p5-10 512 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" -0.5 3500000 3092 ) &   # ~1.1 h
( run add3-p512c16-nnf-m0p5-11 512 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" -0.5 3500000 3093 ) &   # ~1.1 h
( run add3-p512c16-v2f-m0p5-0 512 "R=0.1,C16" "NN v2 + CRC search (first pass)" -0.5 3500000 3111 ) &   # ~1.1 h
( run add3-p512c16-v2f-m0p5-1 512 "R=0.1,C16" "NN v2 + CRC search (first pass)" -0.5 3500000 3112 ) &   # ~1.1 h
( run add3-p512c16-v2f-m0p5-2 512 "R=0.1,C16" "NN v2 + CRC search (first pass)" -0.5 3500000 3113 ) &   # ~1.1 h
( run add3-p512c16-v2f-m0p5-3 512 "R=0.1,C16" "NN v2 + CRC search (first pass)" -0.5 3500000 3114 ) &   # ~1.1 h
( run add3-p512c16-v2f-m0p5-4 512 "R=0.1,C16" "NN v2 + CRC search (first pass)" -0.5 3500000 3115 ) &   # ~1.1 h
( run add3-p512c16-v2f-m0p5-5 512 "R=0.1,C16" "NN v2 + CRC search (first pass)" -0.5 3500000 3116 ) &   # ~1.1 h
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
