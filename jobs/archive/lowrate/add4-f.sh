#!/bin/bash
# add4-f: extra frames ("add4" parts, own seeds) of NN v2 + CRC search (full search) BLER points; 16 single-core lanes, chunks in sequence.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_add4-f.out
PROG=logs/add4-f.progress
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
( run add4-p512c16-v2full-m4-0 512 "R=0.1,C16" "NN v2 + CRC search" -4 483000 4019 ) &   # ~0.9 h
( run add4-p512c16-v2full-m2-0 512 "R=0.1,C16" "NN v2 + CRC search" -2 1875000 4026 ) &   # ~0.9 h
( run add4-p512c16-v2full-m2-1 512 "R=0.1,C16" "NN v2 + CRC search" -2 1875000 4027 ) &   # ~0.9 h
( run add4-p512c16-v2full-m2-2 512 "R=0.1,C16" "NN v2 + CRC search" -2 1875000 4028 ) &   # ~0.9 h
( run add4-p512c16-v2full-m2-3 512 "R=0.1,C16" "NN v2 + CRC search" -2 1875000 4029 ) &   # ~0.9 h
( run add4-p512c11-v2full-m0p5-0 512 "R=0.1" "NN v2 + CRC search" -0.5 2632000 4009 ) &   # ~0.9 h
( run add4-p512c11-v2full-m0p5-1 512 "R=0.1" "NN v2 + CRC search" -0.5 2632000 4010 ) &   # ~0.9 h
( run add4-p512c11-v2full-m0p5-2 512 "R=0.1" "NN v2 + CRC search" -0.5 2632000 4011 ) &   # ~0.9 h
( run add4-p1024c16-v2full-m1-0 1024 "R=0.1,C16" "NN v2 + CRC search" -1 244000 4099 ) &   # ~0.8 h
( run add4-p1024c16-v2full-m1-1 1024 "R=0.1,C16" "NN v2 + CRC search" -1 244000 4100 ) &   # ~0.8 h
( run add4-p1024c16-v2full-m3p5-0 1024 "R=0.1,C16" "NN v2 + CRC search" -3.5 69000 4089 ) &   # ~0.8 h
( run add4-p1024c16-v2full-m3p5-1 1024 "R=0.1,C16" "NN v2 + CRC search" -3.5 69000 4090 ) &   # ~0.8 h
( run add4-p512c11-v2full-m2-0 512 "R=0.1" "NN v2 + CRC search" -2 1667000 4006 ) &   # ~0.8 h
( run add4-p1024c16-v2full-m4-0 1024 "R=0.1,C16" "NN v2 + CRC search" -4 52500 4087 ) &   # ~0.7 h
( run add4-p1024c16-v2full-m4-1 1024 "R=0.1,C16" "NN v2 + CRC search" -4 52500 4088 ) &   # ~0.7 h
( run add4-p1024c16-v2full-m4p5-0 1024 "R=0.1,C16" "NN v2 + CRC search" -4.5 34000 4085 ) &   # ~0.6 h
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
