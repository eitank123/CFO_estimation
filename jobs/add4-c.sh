#!/bin/bash
# add4-c: extra frames ("add4" parts, own seeds) of NN v2 + CRC search (full search) BLER points; 16 single-core lanes, chunks in sequence.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_add4-c.out
PROG=logs/add4-c.progress
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
( run add4-p512c16-v2full-0-3 512 "R=0.1,C16" "NN v2 + CRC search" 0 3429000 4073 ) &   # ~1.1 h
( run add4-p512c16-v2full-0-4 512 "R=0.1,C16" "NN v2 + CRC search" 0 3429000 4074 ) &   # ~1.1 h
( run add4-p512c16-v2full-0-5 512 "R=0.1,C16" "NN v2 + CRC search" 0 3429000 4075 ) &   # ~1.1 h
( run add4-p512c16-v2full-0-6 512 "R=0.1,C16" "NN v2 + CRC search" 0 3429000 4076 ) &   # ~1.1 h
( run add4-p512c16-v2full-0-7 512 "R=0.1,C16" "NN v2 + CRC search" 0 3429000 4077 ) &   # ~1.1 h
( run add4-p512c16-v2full-0-8 512 "R=0.1,C16" "NN v2 + CRC search" 0 3429000 4078 ) &   # ~1.1 h
( run add4-p512c16-v2full-0-9 512 "R=0.1,C16" "NN v2 + CRC search" 0 3429000 4079 ) &   # ~1.1 h
( run add4-p512c16-v2full-0-10 512 "R=0.1,C16" "NN v2 + CRC search" 0 3429000 4080 ) &   # ~1.1 h
( run add4-p512c16-v2full-0-11 512 "R=0.1,C16" "NN v2 + CRC search" 0 3429000 4081 ) &   # ~1.1 h
( run add4-p512c16-v2full-0-12 512 "R=0.1,C16" "NN v2 + CRC search" 0 3429000 4082 ) &   # ~1.1 h
( run add4-p512c16-v2full-0-13 512 "R=0.1,C16" "NN v2 + CRC search" 0 3429000 4083 ) &   # ~1.1 h
( run add4-p512c16-v2full-m2p5-0 512 "R=0.1,C16" "NN v2 + CRC search" -2.5 1786000 4023 ) &   # ~1.1 h
( run add4-p512c16-v2full-m2p5-1 512 "R=0.1,C16" "NN v2 + CRC search" -2.5 1786000 4024 ) &   # ~1.1 h
( run add4-p512c16-v2full-m2p5-2 512 "R=0.1,C16" "NN v2 + CRC search" -2.5 1786000 4025 ) &   # ~1.1 h
( run add4-p512c16-v2full-m1p5-0 512 "R=0.1,C16" "NN v2 + CRC search" -1.5 2727500 4030 ) &   # ~1.1 h
( run add4-p512c16-v2full-m1p5-1 512 "R=0.1,C16" "NN v2 + CRC search" -1.5 2727500 4031 ) &   # ~1.1 h
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
