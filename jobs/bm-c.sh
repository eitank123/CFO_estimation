#!/bin/bash
# bm-c: literature CFO benchmarks, R = 1/2; seeds of st-b/st-c (paired frames)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=small_cfo BLIND_STUDY=small_cfo CFO_MAX=0.03
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_bm-c.out
PROG=logs/bm-c.progress
mkdir -p logs small_cfo/logs small_cfo/results
TOTAL=6
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
  if $PY -u polar_ber_experiment.py --mode ebn0 --packet 1024 --codes "$5" --sources "M&M, est. phase, pre-MF + CRC search (first pass)" "M&M + ML Newton, est. phase, pre-MF + CRC search (first pass)" "ML periodogram (FFT + AM), est. phase, pre-MF + CRC search (first pass)" "M&M + ML Newton, est. phase, pre-MF + code-aided EM" "M&M + ML Newton, est. phase, pre-MF + code-aided EM + CRC search (first pass)" --shared-frames --tag $1 --extra-esn0 $2 --min-errors $6 --max-frames $3 --seed $4 --workers 1 > small_cfo/logs/run_$1.out 2>&1; then finish $1 DONE; else finish $1 "FAILED (exit $?)"; fi
}
( run bm-c-R_1_2_C16-1p5 1.5 200000 18232 "R=1/2,C16" 100 ) &
( run bm-c-R_1_2_C16-2 2 600000 18132 "R=1/2,C16" 100 ) &
( run bm-c-R_1_2_C16-2p5 2.5 1000000 18140 "R=1/2,C16" 100 ) &
( run bm-c-R_1_2_C16-3 3 1000000 18148 "R=1/2,C16" 100 ) &
( run bm-c-R_1_2_C16-3p5 3.5 1000000 18156 "R=1/2,C16" 100 ) &
( run bm-c-R_1_2_C16-4 4 1000000 18164 "R=1/2,C16" 100 ) &
wait
echo "EVAL DONE: all $TOTAL lanes finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
