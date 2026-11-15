#!/bin/bash
# add4-a: extra frames ("add4" parts, own seeds) of NN v2 + CRC search (full search) BLER points; 16 single-core lanes, chunks in sequence.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_add4-a.out
PROG=logs/add4-a.progress
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
( run add4-p512c16-v2full-m0p5-0 512 "R=0.1,C16" "NN v2 + CRC search" -0.5 3429000 4056 ) &   # ~1.1 h
( run add4-p512c16-v2full-m0p5-1 512 "R=0.1,C16" "NN v2 + CRC search" -0.5 3429000 4057 ) &   # ~1.1 h
( run add4-p512c16-v2full-m0p5-2 512 "R=0.1,C16" "NN v2 + CRC search" -0.5 3429000 4058 ) &   # ~1.1 h
( run add4-p512c16-v2full-m0p5-3 512 "R=0.1,C16" "NN v2 + CRC search" -0.5 3429000 4059 ) &   # ~1.1 h
( run add4-p512c16-v2full-m0p5-4 512 "R=0.1,C16" "NN v2 + CRC search" -0.5 3429000 4060 ) &   # ~1.1 h
( run add4-p512c16-v2full-m0p5-5 512 "R=0.1,C16" "NN v2 + CRC search" -0.5 3429000 4061 ) &   # ~1.1 h
( run add4-p512c16-v2full-m0p5-6 512 "R=0.1,C16" "NN v2 + CRC search" -0.5 3429000 4062 ) &   # ~1.1 h
( run add4-p512c16-v2full-m0p5-7 512 "R=0.1,C16" "NN v2 + CRC search" -0.5 3429000 4063 ) &   # ~1.1 h
( run add4-p512c16-v2full-m0p5-8 512 "R=0.1,C16" "NN v2 + CRC search" -0.5 3429000 4064 ) &   # ~1.1 h
( run add4-p512c16-v2full-m0p5-9 512 "R=0.1,C16" "NN v2 + CRC search" -0.5 3429000 4065 ) &   # ~1.1 h
( run add4-p512c16-v2full-m0p5-10 512 "R=0.1,C16" "NN v2 + CRC search" -0.5 3429000 4066 ) &   # ~1.1 h
( run add4-p512c16-v2full-m0p5-11 512 "R=0.1,C16" "NN v2 + CRC search" -0.5 3429000 4067 ) &   # ~1.1 h
( run add4-p512c16-v2full-m0p5-12 512 "R=0.1,C16" "NN v2 + CRC search" -0.5 3429000 4068 ) &   # ~1.1 h
( run add4-p512c16-v2full-m0p5-13 512 "R=0.1,C16" "NN v2 + CRC search" -0.5 3429000 4069 ) &   # ~1.1 h
( run add4-p512c16-v2full-m1-0 512 "R=0.1,C16" "NN v2 + CRC search" -1 3200000 4041 ) &   # ~1.1 h
( run add4-p512c16-v2full-m1-1 512 "R=0.1,C16" "NN v2 + CRC search" -1 3200000 4042 ) &   # ~1.1 h
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
