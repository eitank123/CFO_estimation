#!/bin/bash
# add6-a: extra genie (known CFO) frames ("add6" parts, own seeds); 16 single-core lanes, chunks in sequence.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_add6-a.out
PROG=logs/add6-a.progress
TOTAL=17
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
( run add6-p1024c16-genie-m3p5-9 1024 "R=0.1,C16" "Genie (known CFO)" -3.5 1000000 6032 ) &   # ~0.5 h
( run add6-p1024c16-genie-m3p5-8 1024 "R=0.1,C16" "Genie (known CFO)" -3.5 1000000 6031 ) &   # ~0.5 h
( run add6-p1024c16-genie-m3p5-7 1024 "R=0.1,C16" "Genie (known CFO)" -3.5 1000000 6030 ) &   # ~0.5 h
( run add6-p1024c16-genie-m3p5-6 1024 "R=0.1,C16" "Genie (known CFO)" -3.5 1000000 6029 ) &   # ~0.5 h
( run add6-p1024c16-genie-m3p5-5 1024 "R=0.1,C16" "Genie (known CFO)" -3.5 1000000 6028 ) &   # ~0.5 h
( run add6-p1024c16-genie-m3p5-4 1024 "R=0.1,C16" "Genie (known CFO)" -3.5 1000000 6027 ) &   # ~0.5 h
( run add6-p1024c16-genie-m3p5-3 1024 "R=0.1,C16" "Genie (known CFO)" -3.5 1000000 6026 ) &   # ~0.5 h
( run add6-p1024c16-genie-m3p5-2 1024 "R=0.1,C16" "Genie (known CFO)" -3.5 1000000 6025 ) &   # ~0.5 h
( run add6-p1024c16-genie-m3p5-14 1024 "R=0.1,C16" "Genie (known CFO)" -3.5 1000000 6037 ) &   # ~0.5 h
( run add6-p1024c16-genie-m3p5-13 1024 "R=0.1,C16" "Genie (known CFO)" -3.5 1000000 6036 ) &   # ~0.5 h
( run add6-p1024c16-genie-m3p5-12 1024 "R=0.1,C16" "Genie (known CFO)" -3.5 1000000 6035 ) &   # ~0.5 h
( run add6-p1024c16-genie-m3p5-11 1024 "R=0.1,C16" "Genie (known CFO)" -3.5 1000000 6034 ) &   # ~0.5 h
( run add6-p1024c16-genie-m3p5-10 1024 "R=0.1,C16" "Genie (known CFO)" -3.5 1000000 6033 ) &   # ~0.5 h
( run add6-p1024c16-genie-m3p5-1 1024 "R=0.1,C16" "Genie (known CFO)" -3.5 1000000 6024 ) &   # ~0.5 h
( run add6-p1024c16-genie-m3p5-0 1024 "R=0.1,C16" "Genie (known CFO)" -3.5 1000000 6023 ) &   # ~0.5 h
( run add6-p512c16-genie-m2p5-6 512 "R=0.1,C16" "Genie (known CFO)" -2.5 2142857 6019; run add6-p1024c16-genie-m4p5-0 1024 "R=0.1,C16" "Genie (known CFO)" -4.5 200000 6020 ) &   # ~0.6 h
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
