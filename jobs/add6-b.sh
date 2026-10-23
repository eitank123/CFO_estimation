#!/bin/bash
# add6-b: extra genie (known CFO) frames ("add6" parts, own seeds); 16 single-core lanes, chunks in sequence.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_add6-b.out
PROG=logs/add6-b.progress
TOTAL=20
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
( run add6-p512c16-genie-m2p5-5 512 "R=0.1,C16" "Genie (known CFO)" -2.5 2142857 6018; run add6-p512c16-genie-m4p0-0 512 "R=0.1,C16" "Genie (known CFO)" -4.0 100000 6009 ) &   # ~0.5 h
( run add6-p512c16-genie-m2p5-4 512 "R=0.1,C16" "Genie (known CFO)" -2.5 2142857 6017 ) &   # ~0.5 h
( run add6-p512c16-genie-m2p5-3 512 "R=0.1,C16" "Genie (known CFO)" -2.5 2142857 6016 ) &   # ~0.5 h
( run add6-p512c16-genie-m2p5-2 512 "R=0.1,C16" "Genie (known CFO)" -2.5 2142857 6015 ) &   # ~0.5 h
( run add6-p512c16-genie-m2p5-1 512 "R=0.1,C16" "Genie (known CFO)" -2.5 2142857 6014 ) &   # ~0.5 h
( run add6-p512c16-genie-m2p5-0 512 "R=0.1,C16" "Genie (known CFO)" -2.5 2142857 6013 ) &   # ~0.5 h
( run add6-p512c11-genie-m3p0-6 512 "R=0.1" "Genie (known CFO)" -3.0 2142857 6008 ) &   # ~0.5 h
( run add6-p512c11-genie-m3p0-5 512 "R=0.1" "Genie (known CFO)" -3.0 2142857 6007 ) &   # ~0.5 h
( run add6-p512c11-genie-m3p0-4 512 "R=0.1" "Genie (known CFO)" -3.0 2142857 6006 ) &   # ~0.5 h
( run add6-p512c11-genie-m3p0-3 512 "R=0.1" "Genie (known CFO)" -3.0 2142857 6005 ) &   # ~0.5 h
( run add6-p512c11-genie-m3p0-2 512 "R=0.1" "Genie (known CFO)" -3.0 2142857 6004 ) &   # ~0.5 h
( run add6-p512c11-genie-m3p0-1 512 "R=0.1" "Genie (known CFO)" -3.0 2142857 6003 ) &   # ~0.5 h
( run add6-p512c11-genie-m3p0-0 512 "R=0.1" "Genie (known CFO)" -3.0 2142857 6002 ) &   # ~0.5 h
( run add6-p512c11-genie-m3p5-0 512 "R=0.1" "Genie (known CFO)" -3.5 2000000 6001; run add6-p512c16-genie-m3p5-0 512 "R=0.1,C16" "Genie (known CFO)" -3.5 500000 6010 ) &   # ~0.6 h
( run add6-p1024c16-genie-m4p0-1 1024 "R=0.1,C16" "Genie (known CFO)" -4.0 750000 6022; run add6-p512c16-genie-m3p0-1 512 "R=0.1,C16" "Genie (known CFO)" -3.0 1250000 6012 ) &   # ~0.7 h
( run add6-p1024c16-genie-m4p0-0 1024 "R=0.1,C16" "Genie (known CFO)" -4.0 750000 6021; run add6-p512c16-genie-m3p0-0 512 "R=0.1,C16" "Genie (known CFO)" -3.0 1250000 6011 ) &   # ~0.7 h
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
