#!/bin/bash
# re-b: split ML + the re-encoding check at R = 1/10, more packets (add lanes pooled into re-a2)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=small_cfo BLIND_STUDY=small_cfo CFO_MAX=0.03
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_re-b.out
PROG=logs/re-b.progress
mkdir -p logs small_cfo/logs small_cfo/results
TOTAL=13
T0=$(date +%s)
: > "$PROG"
echo "$(date "+%F %T") start, $TOTAL lanes" > "$LOG"
finish() {
  echo "$(date "+%F %T") $2 $1" >> "$LOG"
  until mkdir "$PROG.lock" 2>/dev/null; do sleep 1; done
  echo $(( $(wc -l < "$PROG") + 1 )) $TOTAL $(( $(date +%s) - T0 )) >> "$PROG"
  rmdir "$PROG.lock"
}
run() {  # tag esn0 frames seed code
  if $PY -u polar_ber_experiment.py --mode ebn0 --packet 1024 --codes "$5" --sources "Split pilots ML, est. phase, pre-MF + CRC search (first pass) + re-encode check" --shared-frames --tag $1 --extra-esn0 $2 --min-errors 1000 --max-frames $3 --seed $4 --workers 1 > small_cfo/logs/run_$1.out 2>&1; then finish $1 DONE; else finish $1 "FAILED (exit $?)"; fi
}
( run re-R_0p1_C16-m5 -5 25000 18000 "R=0.1,C16" ) &
( run add-re2-R_0p1_C16-m5-1 -5 100000 108001 "R=0.1,C16" ) &
( run add-re2-R_0p1_C16-m5-2 -5 100000 108002 "R=0.1,C16" ) &
( run add-re2-R_0p1_C16-m5-3 -5 100000 108003 "R=0.1,C16" ) &
( run add-re2-R_0p1_C16-m5-4 -5 100000 108004 "R=0.1,C16" ) &
( run add-re2-R_0p1_C16-m5-5 -5 100000 108005 "R=0.1,C16" ) &
( run add-re2-R_0p1_C16-m4p5-1 -4.5 100000 108217 "R=0.1,C16" ) &
( run add-re2-R_0p1_C16-m4p5-2 -4.5 100000 108218 "R=0.1,C16" ) &
( run add-re2-R_0p1_C16-m4p5-3 -4.5 100000 108219 "R=0.1,C16" ) &
( run add-re2-R_0p1_C16-m4p5-4 -4.5 100000 108220 "R=0.1,C16" ) &
( run add-re2-R_0p1_C16-m4-1 -4 100000 108009 "R=0.1,C16" ) &
( run add-re2-R_0p1_C16-m4-2 -4 100000 108010 "R=0.1,C16" ) &
( run add-re2-R_0p1_C16-m4-3 -4 100000 108011 "R=0.1,C16" ) &
( run add-re2-R_0p1_C16-m4-4 -4 100000 108012 "R=0.1,C16" ) &
wait
echo "EVAL DONE: all $TOTAL lanes finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
