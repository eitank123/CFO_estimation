#!/bin/bash
# add3-g: extra frames ("add3" parts, own seeds) for jittery BLER points; 16 single-core lanes, chunks in sequence.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_add3-g.out
PROG=logs/add3-g.progress
TOTAL=17
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

( run add3-p512c16-v2f-m1-2 512 "R=0.1,C16" "NN v2 + CRC search (first pass)" -1 3375000 3125 ) &   # ~1.1 h
( run add3-p512c16-v2f-m1-3 512 "R=0.1,C16" "NN v2 + CRC search (first pass)" -1 3375000 3126 ) &   # ~1.1 h
( run add3-p512c16-v2f-m1-4 512 "R=0.1,C16" "NN v2 + CRC search (first pass)" -1 3375000 3127 ) &   # ~1.1 h
( run add3-p512c16-v2f-m1-5 512 "R=0.1,C16" "NN v2 + CRC search (first pass)" -1 3375000 3128 ) &   # ~1.1 h
( run add3-p512c16-v2f-m1-6 512 "R=0.1,C16" "NN v2 + CRC search (first pass)" -1 3375000 3129 ) &   # ~1.1 h
( run add3-p512c16-v2f-m1-7 512 "R=0.1,C16" "NN v2 + CRC search (first pass)" -1 3375000 3130 ) &   # ~1.1 h
( run add3-p512c16-mmf-m1-0 512 "R=0.1,C16" "M&M + CRC search (first pass)" -1 3286000 3065 ) &   # ~1.1 h
( run add3-p512c16-mmf-m1-1 512 "R=0.1,C16" "M&M + CRC search (first pass)" -1 3286000 3066 ) &   # ~1.1 h
( run add3-p512c16-mmf-m1-2 512 "R=0.1,C16" "M&M + CRC search (first pass)" -1 3286000 3067 ) &   # ~1.1 h
( run add3-p512c16-nnfull-m0p5-0 512 "R=0.1,C16" "SNR-aware NN + CRC search" -0.5 3282500 3018 ) &   # ~1.1 h
( run add3-p512c16-nnfull-m0p5-1 512 "R=0.1,C16" "SNR-aware NN + CRC search" -0.5 3282500 3019 ) &   # ~1.1 h
( run add3-p512c16-nnfull-m0p5-2 512 "R=0.1,C16" "SNR-aware NN + CRC search" -0.5 3282500 3020 ) &   # ~1.1 h
( run add3-p512c16-nnfull-m0p5-3 512 "R=0.1,C16" "SNR-aware NN + CRC search" -0.5 3282500 3021 ) &   # ~1.1 h
( run add3-p512c16-nnfull-m0p5-4 512 "R=0.1,C16" "SNR-aware NN + CRC search" -0.5 3282500 3022 ) &   # ~1.1 h
( run add3-p512c16-nnfull-m0p5-5 512 "R=0.1,C16" "SNR-aware NN + CRC search" -0.5 3282500 3023 ) &   # ~1.1 h
( run add3-p512c16-nnfull-m1-0 512 "R=0.1,C16" "SNR-aware NN + CRC search" -1 3030000 3024; run add3-p512c11-nnf-m1p5-0 512 "R=0.1" "SNR-aware NN + CRC search (first pass)" -1.5 174000 3032 ) &   # ~1.0 h
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
