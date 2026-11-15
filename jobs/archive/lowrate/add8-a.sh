#!/bin/bash
# add8-a: split-pilot NN (1024) + CRC full search ("add6" parts, own seeds); 16 single-core lanes, chunks in sequence.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_add8-a.out
PROG=logs/add8-a.progress
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
( run add8-p1024c16-snnfull-m4p0-3 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -4.0 51500 8063 ) &   # ~0.50 h
( run add8-p1024c16-snnfull-m4p0-2 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -4.0 51500 8062 ) &   # ~0.50 h
( run add8-p1024c16-snnfull-m4p0-1 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -4.0 51500 8061 ) &   # ~0.50 h
( run add8-p1024c16-snnfull-m4p0-0 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -4.0 51500 8060 ) &   # ~0.50 h
( run add8-p1024c16-snnfull-m3p0-6 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -3.0 73715 8053 ) &   # ~0.50 h
( run add8-p1024c16-snnfull-m3p0-5 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -3.0 73715 8052 ) &   # ~0.50 h
( run add8-p1024c16-snnfull-m3p0-4 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -3.0 73715 8051 ) &   # ~0.50 h
( run add8-p1024c16-snnfull-m3p0-3 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -3.0 73715 8050 ) &   # ~0.50 h
( run add8-p1024c16-snnfull-m3p0-2 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -3.0 73715 8049 ) &   # ~0.50 h
( run add8-p1024c16-snnfull-m3p0-1 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -3.0 73715 8048 ) &   # ~0.50 h
( run add8-p1024c16-snnfull-m3p0-0 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -3.0 73715 8047 ) &   # ~0.50 h
( run add8-p1024c16-snnfull-m2p0-5 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -2.0 93250 8039 ) &   # ~0.49 h
( run add8-p1024c16-snnfull-m2p0-4 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -2.0 93250 8038 ) &   # ~0.49 h
( run add8-p1024c16-snnfull-m2p0-3 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -2.0 93250 8037 ) &   # ~0.49 h
( run add8-p1024c16-snnfull-m2p0-2 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -2.0 93250 8036 ) &   # ~0.49 h
( run add8-p1024c16-snnfull-m2p0-1 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -2.0 93250 8035 ) &   # ~0.49 h
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
