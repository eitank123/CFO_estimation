#!/bin/bash
# bm2-a: classic fine estimators + split pilots with the estimated phase, R = 1/10 (base lanes on the bm-a seeds, add lanes pooled)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=small_cfo BLIND_STUDY=small_cfo CFO_MAX=0.03
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_bm2-a.out
PROG=logs/bm2-a.progress
mkdir -p logs small_cfo/logs small_cfo/results
TOTAL=15
T0=$(date +%s)
: > "$PROG"
echo "$(date "+%F %T") start, $TOTAL lanes" > "$LOG"
finish() {
  echo "$(date "+%F %T") $2 $1" >> "$LOG"
  until mkdir "$PROG.lock" 2>/dev/null; do sleep 1; done
  echo $(( $(wc -l < "$PROG") + 1 )) $TOTAL $(( $(date +%s) - T0 )) >> "$PROG"
  rmdir "$PROG.lock"
}
run() {  # tag esn0 frames seed code min-errors
  if $PY -u polar_ber_experiment.py --mode ebn0 --packet 1024 --codes "$5" --sources "M&M + L&R, est. phase, pre-MF + CRC search (first pass)" "M&M + Fitz, est. phase, pre-MF + CRC search (first pass)" "Kay, est. phase, pre-MF + CRC search (first pass)" "Split pilots ML, est. phase, pre-MF + CRC search (first pass)" "Split pilots NN, est. phase, pre-MF + CRC search (first pass)" --shared-frames --tag $1 --extra-esn0 $2 --min-errors $6 --max-frames $3 --seed $4 --workers 1 > small_cfo/logs/run_$1.out 2>&1; then finish $1 DONE; else finish $1 "FAILED (exit $?)"; fi
}
( run bm2-R_0p1_C16-m5 -5 120000 18000 "R=0.1,C16" 25 ) &
( run add-bm2-R_0p1_C16-m5-1 -5 120000 68001 "R=0.1,C16" 25 ) &
( run add-bm2-R_0p1_C16-m5-2 -5 120000 68002 "R=0.1,C16" 25 ) &
( run add-bm2-R_0p1_C16-m5-3 -5 120000 68003 "R=0.1,C16" 25 ) &
( run add-bm2-R_0p1_C16-m5-4 -5 120000 68004 "R=0.1,C16" 25 ) &
( run bm2-R_0p1_C16-m4p5 -4.5 120000 18216 "R=0.1,C16" 25 ) &
( run add-bm2-R_0p1_C16-m4p5-1 -4.5 120000 68217 "R=0.1,C16" 25 ) &
( run add-bm2-R_0p1_C16-m4p5-2 -4.5 120000 68218 "R=0.1,C16" 25 ) &
( run add-bm2-R_0p1_C16-m4p5-3 -4.5 120000 68219 "R=0.1,C16" 25 ) &
( run add-bm2-R_0p1_C16-m4p5-4 -4.5 120000 68220 "R=0.1,C16" 25 ) &
( run bm2-R_0p1_C16-m4 -4 120000 18008 "R=0.1,C16" 25 ) &
( run add-bm2-R_0p1_C16-m4-1 -4 120000 68009 "R=0.1,C16" 25 ) &
( run add-bm2-R_0p1_C16-m4-2 -4 120000 68010 "R=0.1,C16" 25 ) &
( run add-bm2-R_0p1_C16-m4-3 -4 120000 68011 "R=0.1,C16" 25 ) &
( run add-bm2-R_0p1_C16-m4-4 -4 120000 68012 "R=0.1,C16" 25 ) &
wait
echo "EVAL DONE: all $TOTAL lanes finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
