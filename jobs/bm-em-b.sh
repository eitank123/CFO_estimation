#!/bin/bash
# bm-em-b: the code-aided EM benchmarks again (re-encoding fix: the decoded path's own CRC bits), same seeds as bm-b
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=small_cfo BLIND_STUDY=small_cfo CFO_MAX=0.03
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_bm-em-b.out
PROG=logs/bm-em-b.progress
mkdir -p logs small_cfo/logs small_cfo/results
TOTAL=7
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
  if $PY -u polar_ber_experiment.py --mode ebn0 --packet 1024 --codes "$5" --sources "M&M + ML Newton, est. phase, pre-MF + code-aided EM" "M&M + ML Newton, est. phase, pre-MF + code-aided EM + CRC search (first pass)" --shared-frames --tag $1 --extra-esn0 $2 --min-errors $6 --max-frames $3 --seed $4 --workers 1 > small_cfo/logs/run_$1.out 2>&1; then finish $1 DONE; else finish $1 "FAILED (exit $?)"; fi
}
( run bm-em-b-R_2_5_C16-0 0 200000 18224 "R=2/5,C16" 100 ) &
( run bm-em-b-R_2_5_C16-0p5 0.5 400000 18048 "R=2/5,C16" 100 ) &
( run bm-em-b-R_2_5_C16-1 1 1000000 18056 "R=2/5,C16" 100 ) &
( run bm-em-b-R_2_5_C16-1p5 1.5 1000000 18064 "R=2/5,C16" 100 ) &
( run bm-em-b-R_2_5_C16-2 2 1000000 18100 "R=2/5,C16" 100 ) &
( run bm-em-b-R_2_5_C16-2p5 2.5 1000000 18108 "R=2/5,C16" 100 ) &
( run bm-em-b-R_2_5_C16-3 3 1000000 18116 "R=2/5,C16" 100 ) &
wait
echo "EVAL DONE: all $TOTAL lanes finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
