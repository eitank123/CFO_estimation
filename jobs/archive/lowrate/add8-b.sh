#!/bin/bash
# add8-b: split-pilot NN (1024) + CRC full search ("add6" parts, own seeds); 16 single-core lanes, chunks in sequence.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_add8-b.out
PROG=logs/add8-b.progress
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
( run add8-p1024c16-snnfull-m2p0-0 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -2.0 93250 8034 ) &   # ~0.49 h
( run add8-p1024c16-snnfull-m1p0-3 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -1.0 146250 8023 ) &   # ~0.49 h
( run add8-p1024c16-snnfull-m1p0-2 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -1.0 146250 8022 ) &   # ~0.49 h
( run add8-p1024c16-snnfull-m1p0-1 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -1.0 146250 8021 ) &   # ~0.49 h
( run add8-p1024c16-snnfull-m1p0-0 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -1.0 146250 8020 ) &   # ~0.49 h
( run add8-p1024c16-snnfull-m0p5-9 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -0.5 167182 8018 ) &   # ~0.48 h
( run add8-p1024c16-snnfull-m0p5-8 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -0.5 167182 8017 ) &   # ~0.48 h
( run add8-p1024c16-snnfull-m0p5-7 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -0.5 167182 8016 ) &   # ~0.48 h
( run add8-p1024c16-snnfull-m0p5-6 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -0.5 167182 8015 ) &   # ~0.48 h
( run add8-p1024c16-snnfull-m0p5-5 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -0.5 167182 8014 ) &   # ~0.48 h
( run add8-p1024c16-snnfull-m0p5-4 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -0.5 167182 8013 ) &   # ~0.48 h
( run add8-p1024c16-snnfull-m0p5-3 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -0.5 167182 8012 ) &   # ~0.48 h
( run add8-p1024c16-snnfull-m0p5-2 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -0.5 167182 8011 ) &   # ~0.48 h
( run add8-p1024c16-snnfull-m0p5-10 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -0.5 167182 8019 ) &   # ~0.48 h
( run add8-p1024c16-snnfull-m0p5-1 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -0.5 167182 8010 ) &   # ~0.48 h
( run add8-p1024c16-snnfull-m0p5-0 1024 "R=0.1,C16" "Split pilots NN, quarter + CRC search" -0.5 167182 8009 ) &   # ~0.48 h
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
