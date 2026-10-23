#!/bin/bash
# add4-e: extra frames ("add4" parts, own seeds) of NN v2 + CRC search (full search) BLER points; 16 single-core lanes, chunks in sequence.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_add4-e.out
PROG=logs/add4-e.progress
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
( run add4-p1024c16-v2full-m1p5-0 1024 "R=0.1,C16" "NN v2 + CRC search" -1.5 225500 4097 ) &   # ~1.0 h
( run add4-p1024c16-v2full-m1p5-1 1024 "R=0.1,C16" "NN v2 + CRC search" -1.5 225500 4098 ) &   # ~1.0 h
( run add4-p1024c16-v2full-m5-0 1024 "R=0.1,C16" "NN v2 + CRC search" -5 48500 4084 ) &   # ~1.0 h
( run add4-p1024c16-v2full-m0p5-0 1024 "R=0.1,C16" "NN v2 + CRC search" -0.5 396000 4101 ) &   # ~1.0 h
( run add4-p1024c16-v2full-m0p5-1 1024 "R=0.1,C16" "NN v2 + CRC search" -0.5 396000 4102 ) &   # ~1.0 h
( run add4-p512c16-v2full-m3p5-0 512 "R=0.1,C16" "NN v2 + CRC search" -3.5 807500 4020 ) &   # ~1.0 h
( run add4-p512c11-v2full-m1-0 512 "R=0.1" "NN v2 + CRC search" -1 2860000 4008 ) &   # ~1.0 h
( run add4-p512c11-v2full-m1p5-0 512 "R=0.1" "NN v2 + CRC search" -1.5 2584500 4007 ) &   # ~1.0 h
( run add4-p512c16-v2full-m3-0 512 "R=0.1,C16" "NN v2 + CRC search" -3 1071500 4021 ) &   # ~1.0 h
( run add4-p512c16-v2full-m3-1 512 "R=0.1,C16" "NN v2 + CRC search" -3 1071500 4022 ) &   # ~1.0 h
( run add4-p1024c16-v2full-m2p5-0 1024 "R=0.1,C16" "NN v2 + CRC search" -2.5 126500 4093 ) &   # ~0.9 h
( run add4-p1024c16-v2full-m2p5-1 1024 "R=0.1,C16" "NN v2 + CRC search" -2.5 126500 4094 ) &   # ~0.9 h
( run add4-p1024c16-v2full-m3-0 1024 "R=0.1,C16" "NN v2 + CRC search" -3 96500 4091 ) &   # ~0.9 h
( run add4-p1024c16-v2full-m3-1 1024 "R=0.1,C16" "NN v2 + CRC search" -3 96500 4092 ) &   # ~0.9 h
( run add4-p1024c16-v2full-m2-0 1024 "R=0.1,C16" "NN v2 + CRC search" -2 155500 4095 ) &   # ~0.9 h
( run add4-p1024c16-v2full-m2-1 1024 "R=0.1,C16" "NN v2 + CRC search" -2 155500 4096 ) &   # ~0.9 h
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
