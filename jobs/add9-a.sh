#!/bin/bash
# add9-a: R=1/4 CRC-16 (1024 symbols), M&M and the split-pilot NN with / without the CRC search (first pass) + genie,
# SNR 0 .. 10 dB, first look (200000 frames or 300 errors per point); one chunk per lane.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_add9-a.out
PROG=logs/add9-a.progress
TOTAL=15
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
  if $PY -u polar_ber_experiment.py --mode ebn0 --packet $2 --codes "$3" --sources "$4" --tag $1 --extra-esn0 $5 --min-errors 300 --max-frames $6 --seed $7 --workers 1 > lowrate/logs/run_$1.out 2>&1; then finish $1 DONE; else finish $1 "FAILED (exit $?)"; fi
}

( run add9-p1024r14-genie-0p0 1024 "R=1/4,C16" "Genie (known CFO)" 0.0 200000 9000 ) &
( run add9-p1024r14-genie-0p5 1024 "R=1/4,C16" "Genie (known CFO)" 0.5 200000 9005 ) &
( run add9-p1024r14-genie-1p0 1024 "R=1/4,C16" "Genie (known CFO)" 1.0 200000 9010 ) &
( run add9-p1024r14-genie-1p5 1024 "R=1/4,C16" "Genie (known CFO)" 1.5 200000 9015 ) &
( run add9-p1024r14-genie-2p0 1024 "R=1/4,C16" "Genie (known CFO)" 2.0 200000 9020 ) &
( run add9-p1024r14-genie-2p5 1024 "R=1/4,C16" "Genie (known CFO)" 2.5 200000 9025 ) &
( run add9-p1024r14-genie-3p0 1024 "R=1/4,C16" "Genie (known CFO)" 3.0 200000 9030 ) &
( run add9-p1024r14-genie-4p0 1024 "R=1/4,C16" "Genie (known CFO)" 4.0 200000 9035 ) &
( run add9-p1024r14-genie-5p0 1024 "R=1/4,C16" "Genie (known CFO)" 5.0 200000 9040 ) &
( run add9-p1024r14-genie-6p0 1024 "R=1/4,C16" "Genie (known CFO)" 6.0 200000 9045 ) &
( run add9-p1024r14-genie-7p0 1024 "R=1/4,C16" "Genie (known CFO)" 7.0 200000 9050 ) &
( run add9-p1024r14-genie-8p0 1024 "R=1/4,C16" "Genie (known CFO)" 8.0 200000 9055 ) &
( run add9-p1024r14-genie-9p0 1024 "R=1/4,C16" "Genie (known CFO)" 9.0 200000 9060 ) &
( run add9-p1024r14-genie-10p0 1024 "R=1/4,C16" "Genie (known CFO)" 10.0 200000 9065 ) &
( run add9-p1024r13-genie-0p0 1024 "R=1/3,C16" "Genie (known CFO)" 0.0 200000 9070 ) &
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
