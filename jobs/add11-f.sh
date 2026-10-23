#!/bin/bash
# add11-f: R=1/3 CRC-16 (1024 symbols), M&M and the split-pilot NN with / without the CRC search (first pass) + genie,
# SNR 0 .. 10 dB, top-up (500000 frames or 100 errors per point); one chunk per lane.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_add11-f.out
PROG=logs/add11-f.progress
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
  if $PY -u polar_ber_experiment.py --mode ebn0 --packet $2 --codes "$3" --sources "$4" --tag $1 --extra-esn0 $5 --min-errors 100 --max-frames $6 --seed $7 --workers 1 > lowrate/logs/run_$1.out 2>&1; then finish $1 DONE; else finish $1 "FAILED (exit $?)"; fi
}

( run add11-p1024r13-genie-2p0-0 1024 "R=1/3,C16" "Genie (known CFO)" 2.0 500000 11005 ) &
( run add11-p1024r13-genie-3p0-2 1024 "R=1/3,C16" "Genie (known CFO)" 3.0 500000 11013 ) &
( run add11-p1024r13-mm-4p0-0 1024 "R=1/3,C16" "M&M" 4.0 500000 11021 ) &
( run add11-p1024r13-mm-8p0-0 1024 "R=1/3,C16" "M&M" 8.0 500000 11029 ) &
( run add11-p1024r13-mm-10p0-2 1024 "R=1/3,C16" "M&M" 10.0 500000 11037 ) &
( run add11-p1024r13-snn-4p0-0 1024 "R=1/3,C16" "Split pilots NN, quarter" 4.0 500000 11045 ) &
( run add11-p1024r13-snn-8p0-0 1024 "R=1/3,C16" "Split pilots NN, quarter" 8.0 500000 11053 ) &
( run add11-p1024r13-snn-10p0-2 1024 "R=1/3,C16" "Split pilots NN, quarter" 10.0 500000 11061 ) &
( run add11-p1024r13-mmf-1p0-3 1024 "R=1/3,C16" "M&M + CRC search (first pass)" 1.0 500000 11069 ) &
( run add11-p1024r13-mmf-2p0-3 1024 "R=1/3,C16" "M&M + CRC search (first pass)" 2.0 500000 11077 ) &
( run add11-p1024r13-mmf-3p0-3 1024 "R=1/3,C16" "M&M + CRC search (first pass)" 3.0 500000 11085 ) &
( run add11-p1024r13-snnf-0p5-0 1024 "R=1/3,C16" "Split pilots NN, quarter + CRC search (first pass)" 0.5 500000 11093 ) &
( run add11-p1024r13-snnf-1p5-0 1024 "R=1/3,C16" "Split pilots NN, quarter + CRC search (first pass)" 1.5 500000 11101 ) &
( run add11-p1024r13-snnf-2p5-0 1024 "R=1/3,C16" "Split pilots NN, quarter + CRC search (first pass)" 2.5 500000 11109 ) &
( run add11-p1024r13-snnf-4p0-0 1024 "R=1/3,C16" "Split pilots NN, quarter + CRC search (first pass)" 4.0 500000 11117 ) &
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
