#!/bin/bash
# add4-b: extra frames ("add4" parts, own seeds) of NN v2 + CRC search (full search) BLER points; 16 single-core lanes, chunks in sequence.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_add4-b.out
PROG=logs/add4-b.progress
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
( run add4-p512c16-v2full-m1-2 512 "R=0.1,C16" "NN v2 + CRC search" -1 3200000 4043 ) &   # ~1.1 h
( run add4-p512c16-v2full-m1-3 512 "R=0.1,C16" "NN v2 + CRC search" -1 3200000 4044 ) &   # ~1.1 h
( run add4-p512c16-v2full-m1-4 512 "R=0.1,C16" "NN v2 + CRC search" -1 3200000 4045 ) &   # ~1.1 h
( run add4-p512c16-v2full-m1-5 512 "R=0.1,C16" "NN v2 + CRC search" -1 3200000 4046 ) &   # ~1.1 h
( run add4-p512c16-v2full-m1-6 512 "R=0.1,C16" "NN v2 + CRC search" -1 3200000 4047 ) &   # ~1.1 h
( run add4-p512c16-v2full-m1-7 512 "R=0.1,C16" "NN v2 + CRC search" -1 3200000 4048 ) &   # ~1.1 h
( run add4-p512c16-v2full-m1-8 512 "R=0.1,C16" "NN v2 + CRC search" -1 3200000 4049 ) &   # ~1.1 h
( run add4-p512c16-v2full-m1-9 512 "R=0.1,C16" "NN v2 + CRC search" -1 3200000 4050 ) &   # ~1.1 h
( run add4-p512c16-v2full-m1-10 512 "R=0.1,C16" "NN v2 + CRC search" -1 3200000 4051 ) &   # ~1.1 h
( run add4-p512c16-v2full-m1-11 512 "R=0.1,C16" "NN v2 + CRC search" -1 3200000 4052 ) &   # ~1.1 h
( run add4-p512c16-v2full-m1-12 512 "R=0.1,C16" "NN v2 + CRC search" -1 3200000 4053 ) &   # ~1.1 h
( run add4-p512c16-v2full-m1-13 512 "R=0.1,C16" "NN v2 + CRC search" -1 3200000 4054 ) &   # ~1.1 h
( run add4-p512c16-v2full-m1-14 512 "R=0.1,C16" "NN v2 + CRC search" -1 3200000 4055 ) &   # ~1.1 h
( run add4-p512c16-v2full-0-0 512 "R=0.1,C16" "NN v2 + CRC search" 0 3429000 4070 ) &   # ~1.1 h
( run add4-p512c16-v2full-0-1 512 "R=0.1,C16" "NN v2 + CRC search" 0 3429000 4071 ) &   # ~1.1 h
( run add4-p512c16-v2full-0-2 512 "R=0.1,C16" "NN v2 + CRC search" 0 3429000 4072 ) &   # ~1.1 h
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
