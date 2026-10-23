#!/bin/bash
# add4-d: extra frames ("add4" parts, own seeds) of NN v2 + CRC search (full search) BLER points; 16 single-core lanes, chunks in sequence.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_add4-d.out
PROG=logs/add4-d.progress
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
( run add4-p512c16-v2full-m1p5-2 512 "R=0.1,C16" "NN v2 + CRC search" -1.5 2727500 4032 ) &   # ~1.1 h
( run add4-p512c16-v2full-m1p5-3 512 "R=0.1,C16" "NN v2 + CRC search" -1.5 2727500 4033 ) &   # ~1.1 h
( run add4-p512c16-v2full-m1p5-4 512 "R=0.1,C16" "NN v2 + CRC search" -1.5 2727500 4034 ) &   # ~1.1 h
( run add4-p512c16-v2full-m1p5-5 512 "R=0.1,C16" "NN v2 + CRC search" -1.5 2727500 4035 ) &   # ~1.1 h
( run add4-p512c16-v2full-m1p5-6 512 "R=0.1,C16" "NN v2 + CRC search" -1.5 2727500 4036 ) &   # ~1.1 h
( run add4-p512c16-v2full-m1p5-7 512 "R=0.1,C16" "NN v2 + CRC search" -1.5 2727500 4037 ) &   # ~1.1 h
( run add4-p512c16-v2full-m1p5-8 512 "R=0.1,C16" "NN v2 + CRC search" -1.5 2727500 4038 ) &   # ~1.1 h
( run add4-p512c16-v2full-m1p5-9 512 "R=0.1,C16" "NN v2 + CRC search" -1.5 2727500 4039 ) &   # ~1.1 h
( run add4-p512c16-v2full-m1p5-10 512 "R=0.1,C16" "NN v2 + CRC search" -1.5 2727500 4040 ) &   # ~1.1 h
( run add4-p512c11-v2full-0-0 512 "R=0.1" "NN v2 + CRC search" 0 3333500 4012 ) &   # ~1.1 h
( run add4-p512c11-v2full-0-1 512 "R=0.1" "NN v2 + CRC search" 0 3333500 4013 ) &   # ~1.1 h
( run add4-p512c11-v2full-0-2 512 "R=0.1" "NN v2 + CRC search" 0 3333500 4014 ) &   # ~1.1 h
( run add4-p512c11-v2full-0-3 512 "R=0.1" "NN v2 + CRC search" 0 3333500 4015 ) &   # ~1.1 h
( run add4-p512c11-v2full-0-4 512 "R=0.1" "NN v2 + CRC search" 0 3333500 4016 ) &   # ~1.1 h
( run add4-p1024c16-v2full-0-0 1024 "R=0.1,C16" "NN v2 + CRC search" 0 556000 4103 ) &   # ~1.1 h
( run add4-p1024c16-v2full-0-1 1024 "R=0.1,C16" "NN v2 + CRC search" 0 556000 4104 ) &   # ~1.1 h
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
