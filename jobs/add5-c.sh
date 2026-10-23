#!/bin/bash
# add5-c: extra frames ("add5" parts, own seeds): split pilots (quarter) full search / first pass, NN v2 full search; 16 single-core lanes, chunks in sequence.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_add5-c.out
PROG=logs/add5-c.progress
TOTAL=47
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
( run add5-p512c16-sqf-m2-10 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -2 3423500 5062; run add5-p1024c16-v2full-m4-1 1024 "R=0.1,C16" "NN v2 + CRC search" -4 75000 5214; run add5-p512c16-sqf-m2p5-1 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -2.5 2333500 5042 ) &   # ~2.9 h
( run add5-p512c16-sqf-m2-11 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -2 3423500 5063; run add5-p1024c16-v2full-m4-2 1024 "R=0.1,C16" "NN v2 + CRC search" -4 75000 5215; run add5-p512c16-sqf-m2p5-2 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -2.5 2333500 5043 ) &   # ~2.9 h
( run add5-p512c16-sqf-m2-12 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -2 3423500 5064; run add5-p1024c16-v2full-m4-3 1024 "R=0.1,C16" "NN v2 + CRC search" -4 75000 5216; run add5-p512c11-sqfull-0-0 512 "R=0.1" "Split pilots, quarter (ML) + CRC search" 0 2381000 5020 ) &   # ~2.9 h
( run add5-p512c16-sqfull-0-0 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" 0 3429000 5193; run add5-p512c16-v2full-m2-7 512 "R=0.1,C16" "NN v2 + CRC search" -2 2411000 5089 ) &   # ~2.2 h
( run add5-p512c16-sqfull-0-1 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" 0 3429000 5194; run add5-p512c11-v2full-m0p5-0 512 "R=0.1" "NN v2 + CRC search" -0.5 3090000 5015; run add5-p512c11-v2full-m4-0 512 "R=0.1" "NN v2 + CRC search" -4 167500 5003 ) &   # ~2.4 h
( run add5-p512c16-sqfull-0-2 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" 0 3429000 5195; run add5-p512c11-v2full-m0p5-1 512 "R=0.1" "NN v2 + CRC search" -0.5 3090000 5016; run add5-p512c11-sqfull-m4-0 512 "R=0.1" "Split pilots, quarter (ML) + CRC search" -4 247500 5002 ) &   # ~2.3 h
( run add5-p512c16-sqfull-0-3 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" 0 3429000 5196; run add5-p512c11-v2full-m0p5-2 512 "R=0.1" "NN v2 + CRC search" -0.5 3090000 5017; run add5-p512c11-sqfull-m4p5-0 512 "R=0.1" "Split pilots, quarter (ML) + CRC search" -4.5 60000 5001 ) &   # ~2.2 h
( run add5-p512c16-sqfull-0-4 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" 0 3429000 5197; run add5-p1024c16-v2full-m2-0 1024 "R=0.1,C16" "NN v2 + CRC search" -2 197000 5258; run add5-p512c11-sqf-m1p5-0 512 "R=0.1" "Split pilots, quarter (ML) + CRC search (first pass)" -1.5 1583500 5008 ) &   # ~2.7 h
( run add5-p512c16-sqfull-0-5 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" 0 3429000 5198; run add5-p1024c16-v2full-m2-1 1024 "R=0.1,C16" "NN v2 + CRC search" -2 197000 5259; run add5-p512c16-v2full-m3p5-0 512 "R=0.1,C16" "NN v2 + CRC search" -3.5 495000 5034 ) &   # ~2.6 h
( run add5-p512c16-sqfull-0-6 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" 0 3429000 5199; run add5-p1024c16-v2full-m2-2 1024 "R=0.1,C16" "NN v2 + CRC search" -2 197000 5260; run add5-p512c16-sqfull-m4-0 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -4 546000 5030 ) &   # ~2.5 h
( run add5-p512c16-sqfull-0-7 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" 0 3429000 5200; run add5-p1024c16-v2full-m2-3 1024 "R=0.1,C16" "NN v2 + CRC search" -2 197000 5261; run add5-p512c11-sqfull-m3p5-0 512 "R=0.1" "Split pilots, quarter (ML) + CRC search" -3.5 547500 5004 ) &   # ~2.5 h
( run add5-p512c16-sqfull-0-8 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" 0 3429000 5201; run add5-p1024c16-v2full-m2-4 1024 "R=0.1,C16" "NN v2 + CRC search" -2 197000 5262; run add5-p512c11-sqfull-m3-0 512 "R=0.1" "Split pilots, quarter (ML) + CRC search" -3 606000 5005 ) &   # ~2.5 h
( run add5-p512c16-sqfull-0-9 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" 0 3429000 5202; run add5-p1024c16-v2full-0-0 1024 "R=0.1,C16" "NN v2 + CRC search" 0 587000 5300; run add5-p1024c16-sqfull-m4p5-0 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -4.5 54000 5208 ) &   # ~2.7 h
( run add5-p512c16-sqfull-0-10 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" 0 3429000 5203; run add5-p1024c16-v2full-0-1 1024 "R=0.1,C16" "NN v2 + CRC search" 0 587000 5301; run add5-p1024c16-sqfull-m4p5-1 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -4.5 54000 5209 ) &   # ~2.7 h
( run add5-p512c16-sqfull-0-11 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" 0 3429000 5204; run add5-p1024c16-v2full-0-2 1024 "R=0.1,C16" "NN v2 + CRC search" 0 587000 5302; run add5-p512c11-sqf-m1-0 512 "R=0.1" "Split pilots, quarter (ML) + CRC search (first pass)" -1 1674000 5010 ) &   # ~2.7 h
( run add5-p512c16-sqfull-0-12 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" 0 3429000 5205; run add5-p1024c16-v2full-0-3 1024 "R=0.1,C16" "NN v2 + CRC search" 0 587000 5303; run add5-p1024c16-sqfull-m5-0 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -5 50000 5207 ) &   # ~2.7 h
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
