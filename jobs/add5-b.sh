#!/bin/bash
# add5-b: extra frames ("add5" parts, own seeds): split pilots (quarter) full search / first pass, NN v2 full search; 16 single-core lanes, chunks in sequence.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_add5-b.out
PROG=logs/add5-b.progress
TOTAL=48
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
( run add5-p512c16-sqfull-m2-11 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -2 2824000 5076; run add5-p1024c16-sqfull-m1p5-2 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1.5 234000 5266; run add5-p512c16-sqf-m3p5-0 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -3.5 2290000 5031 ) &   # ~2.9 h
( run add5-p512c16-sqfull-m2-12 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -2 2824000 5077; run add5-p1024c16-sqfull-m1p5-3 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1.5 234000 5267; run add5-p1024c16-sqf-0-0 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" 0 1330500 5296 ) &   # ~2.9 h
( run add5-p512c16-sqfull-m2-13 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -2 2824000 5078; run add5-p1024c16-sqfull-m1p5-4 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1.5 234000 5268; run add5-p1024c16-sqfull-m3p5-0 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -3.5 119500 5217 ) &   # ~2.9 h
( run add5-p512c16-sqfull-m2-14 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -2 2824000 5079; run add5-p512c11-v2full-0-0 512 "R=0.1" "NN v2 + CRC search" 0 2840000 5023; run add5-p512c16-sqfull-m3-0 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -3 1786000 5036 ) &   # ~3.0 h
( run add5-p512c16-sqfull-m2-15 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -2 2824000 5080; run add5-p512c11-v2full-0-1 512 "R=0.1" "NN v2 + CRC search" 0 2840000 5024; run add5-p512c16-sqfull-m3-1 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -3 1786000 5037 ) &   # ~3.0 h
( run add5-p512c16-sqfull-m2-16 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -2 2824000 5081; run add5-p512c11-v2full-0-2 512 "R=0.1" "NN v2 + CRC search" 0 2840000 5025; run add5-p512c16-sqfull-m3-2 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -3 1786000 5038 ) &   # ~3.0 h
( run add5-p512c16-sqf-m2-0 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -2 3423500 5052; run add5-p1024c16-v2full-0-5 1024 "R=0.1,C16" "NN v2 + CRC search" 0 587000 5305; run add5-p512c16-sqfull-m4p5-0 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -4.5 43000 5029 ) &   # ~2.2 h
( run add5-p512c16-sqf-m2-1 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -2 3423500 5053; run add5-p512c11-sqfull-m1p5-0 512 "R=0.1" "Split pilots, quarter (ML) + CRC search" -1.5 2737500 5009; run add5-p512c11-sqfull-m2-0 512 "R=0.1" "Split pilots, quarter (ML) + CRC search" -2 1400500 5007 ) &   # ~2.7 h
( run add5-p512c16-sqf-m2-2 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -2 3423500 5054; run add5-p512c11-sqfull-m1-0 512 "R=0.1" "Split pilots, quarter (ML) + CRC search" -1 2891500 5011; run add5-p512c16-v2full-m3-1 512 "R=0.1,C16" "NN v2 + CRC search" -3 989500 5040 ) &   # ~2.9 h
( run add5-p512c16-sqf-m2-3 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -2 3423500 5055; run add5-p512c11-sqfull-m0p5-0 512 "R=0.1" "Split pilots, quarter (ML) + CRC search" -0.5 2957500 5014; run add5-p512c16-v2full-m3-0 512 "R=0.1,C16" "NN v2 + CRC search" -3 989500 5039 ) &   # ~2.9 h
( run add5-p512c16-sqf-m2-4 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -2 3423500 5056; run add5-p1024c16-sqfull-m1-0 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1 292500 5275; run add5-p512c11-sqf-0-1 512 "R=0.1" "Split pilots, quarter (ML) + CRC search (first pass)" 0 2250000 5019 ) &   # ~2.9 h
( run add5-p512c16-sqf-m2-5 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -2 3423500 5057; run add5-p1024c16-sqfull-m1-1 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1 292500 5276; run add5-p1024c16-sqf-m3-0 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -3 789500 5228 ) &   # ~2.9 h
( run add5-p512c16-sqf-m2-6 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -2 3423500 5058; run add5-p1024c16-sqfull-m2p5-0 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -2.5 171500 5240; run add5-p512c16-sqfull-m3p5-0 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -3.5 1190500 5032 ) &   # ~2.8 h
( run add5-p512c16-sqf-m2-7 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -2 3423500 5059; run add5-p1024c16-sqfull-m2p5-1 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -2.5 171500 5241; run add5-p512c16-sqfull-m3p5-1 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -3.5 1190500 5033 ) &   # ~2.8 h
( run add5-p512c16-sqf-m2-8 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -2 3423500 5060; run add5-p1024c16-sqfull-m2p5-2 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -2.5 171500 5242; run add5-p512c11-sqf-0-0 512 "R=0.1" "Split pilots, quarter (ML) + CRC search (first pass)" 0 2250000 5018 ) &   # ~2.8 h
( run add5-p512c16-sqf-m2-9 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -2 3423500 5061; run add5-p1024c16-v2full-m4-0 1024 "R=0.1,C16" "NN v2 + CRC search" -4 75000 5213; run add5-p512c16-sqf-m2p5-0 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -2.5 2333500 5041 ) &   # ~2.9 h
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
