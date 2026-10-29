#!/bin/bash
# st-c: small-CFO study (CFO_MAX=0.03): 128-pilot split NN (retrained on +-0.03) and M&M on 128 contiguous pilots,
# both with the pre-MF correction + CRC search (first pass), and the pre-MF genie, on shared frames; one lane per point
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=small_cfo BLIND_STUDY=small_cfo CFO_MAX=0.03
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_st-c.out
PROG=logs/st-c.progress
mkdir -p logs small_cfo/logs small_cfo/results
TOTAL=5
# wait (at most 4 h) for the retrained split NN: never run on the +-0.2 model
for i in $(seq 240); do grep -q COPIED logs/run_snn-s1.out 2>/dev/null && [ -f small_cfo/models/cfo_split_nn_L1024.pth ] && break; sleep 60; done
grep -q COPIED logs/run_snn-s1.out 2>/dev/null || { echo "no retrained split NN (snn-s1): not run" > "$LOG"; exit 1; }
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
  if $PY -u polar_ber_experiment.py --mode ebn0 --packet 1024 --codes "$5" --sources "Split pilots NN, quarter, pre-MF correction + CRC search (first pass)" "M&M, pre-MF correction + CRC search (first pass)" "Genie (known CFO), pre-MF correction" --shared-frames --tag $1 --extra-esn0 $2 --min-errors 100 --max-frames $3 --seed $4 --workers 1 > small_cfo/logs/run_$1.out 2>&1; then finish $1 DONE; else finish $1 "FAILED (exit $?)"; fi
}
( run st-c-R_0p1_C16--6 -6 400000 18200 "R=0.1,C16" ) &
( run st-c-R_0p1_C16--5p5 -5.5 400000 18208 "R=0.1,C16" ) &
( run st-c-R_0p1_C16--4p5 -4.5 600000 18216 "R=0.1,C16" ) &
( run st-c-R_2_5_C16-0 0 200000 18224 "R=2/5,C16" ) &
( run st-c-R_1_2_C16-1p5 1.5 200000 18232 "R=1/2,C16" ) &
wait
echo "EVAL DONE: all $TOTAL lanes finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
