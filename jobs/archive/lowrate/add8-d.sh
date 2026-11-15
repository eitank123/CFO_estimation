#!/bin/bash
# add8-d: split-pilot NN (1024) + CRC full search ("add6" parts, own seeds); 16 single-core lanes, chunks in sequence.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_add8-d.out
PROG=logs/add8-d.progress
TOTAL=20
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
( run add8-p1024c16-snnfull-m2p5-6 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -2.5 73500 8046 ) &   # ~0.44 h
( run add8-p1024c16-snnfull-m2p5-5 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -2.5 73500 8045 ) &   # ~0.44 h
( run add8-p1024c16-snnfull-m2p5-4 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -2.5 73500 8044 ) &   # ~0.44 h
( run add8-p1024c16-snnfull-m2p5-3 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -2.5 73500 8043 ) &   # ~0.44 h
( run add8-p1024c16-snnfull-m2p5-2 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -2.5 73500 8042 ) &   # ~0.44 h
( run add8-p1024c16-snnfull-m2p5-1 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -2.5 73500 8041 ) &   # ~0.44 h
( run add8-p1024c16-snnfull-m2p5-0 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -2.5 73500 8040 ) &   # ~0.44 h
( run add8-p1024c16-snnfull-0p0-7 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" 0.0 178688 8008; run add8-p1024c16-snnfull-m4p5-0 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -4.5 36000 8064 ) &   # ~0.82 h
( run add8-p1024c16-snnfull-0p0-6 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" 0.0 178688 8007; run add8-p1024c16-snnfull-m5p0-1 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -5.0 25000 8068 ) &   # ~0.73 h
( run add8-p1024c16-snnfull-0p0-5 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" 0.0 178688 8006; run add8-p1024c16-snnfull-m5p0-0 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -5.0 25000 8067 ) &   # ~0.73 h
( run add8-p1024c16-snnfull-0p0-4 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" 0.0 178688 8005 ) &   # ~0.44 h
( run add8-p1024c16-snnfull-0p0-3 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" 0.0 178688 8004 ) &   # ~0.44 h
( run add8-p1024c16-snnfull-0p0-2 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" 0.0 178688 8003 ) &   # ~0.44 h
( run add8-p1024c16-snnfull-0p0-1 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" 0.0 178688 8002 ) &   # ~0.44 h
( run add8-p1024c16-snnfull-0p0-0 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" 0.0 178688 8001 ) &   # ~0.44 h
( run add8-p1024c16-snnfull-m4p5-2 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -4.5 36000 8066; run add8-p1024c16-snnfull-m4p5-1 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -4.5 36000 8065 ) &   # ~0.76 h
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
