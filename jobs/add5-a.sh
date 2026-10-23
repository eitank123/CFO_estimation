#!/bin/bash
# add5-a: extra frames ("add5" parts, own seeds): split pilots (quarter) full search / first pass, NN v2 full search; 16 single-core lanes, chunks in sequence.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_add5-a.out
PROG=logs/add5-a.progress
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
( run add5-p1024c16-v2full-m0p5-0 1024 "R=0.1,C16" "NN v2 + CRC search" -0.5 502000 5291; run add5-p512c11-v2full-0-3 512 "R=0.1" "NN v2 + CRC search" 0 2840000 5026; run add5-p512c16-v2full-m2p5-0 512 "R=0.1,C16" "NN v2 + CRC search" -2.5 1649000 5049 ) &   # ~2.9 h
( run add5-p1024c16-v2full-m0p5-1 1024 "R=0.1,C16" "NN v2 + CRC search" -0.5 502000 5292; run add5-p512c11-v2full-0-4 512 "R=0.1" "NN v2 + CRC search" 0 2840000 5027; run add5-p512c16-v2full-m2p5-1 512 "R=0.1,C16" "NN v2 + CRC search" -2.5 1649000 5050 ) &   # ~2.9 h
( run add5-p1024c16-v2full-m0p5-2 1024 "R=0.1,C16" "NN v2 + CRC search" -0.5 502000 5293; run add5-p1024c16-sqfull-m3-0 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -3 129000 5229; run add5-p1024c16-sqfull-m3-3 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -3 129000 5232 ) &   # ~3.0 h
( run add5-p1024c16-v2full-m0p5-3 1024 "R=0.1,C16" "NN v2 + CRC search" -0.5 502000 5294; run add5-p1024c16-sqfull-m3-1 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -3 129000 5230; run add5-p1024c16-sqfull-m4-0 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -4 103000 5211 ) &   # ~3.0 h
( run add5-p1024c16-v2full-m0p5-4 1024 "R=0.1,C16" "NN v2 + CRC search" -0.5 502000 5295; run add5-p1024c16-sqfull-m3-2 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -3 129000 5231; run add5-p1024c16-sqfull-m4-1 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -4 103000 5212 ) &   # ~3.0 h
( run add5-p512c16-sqfull-m2-0 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -2 2824000 5065; run add5-p1024c16-v2full-m3-0 1024 "R=0.1,C16" "NN v2 + CRC search" -3 114500 5233; run add5-p512c11-sqfull-0-1 512 "R=0.1" "Split pilots, quarter (ML) + CRC search" 0 2381000 5021 ) &   # ~2.9 h
( run add5-p512c16-sqfull-m2-1 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -2 2824000 5066; run add5-p1024c16-v2full-m3-1 1024 "R=0.1,C16" "NN v2 + CRC search" -3 114500 5234; run add5-p512c11-sqfull-0-2 512 "R=0.1" "Split pilots, quarter (ML) + CRC search" 0 2381000 5022 ) &   # ~2.9 h
( run add5-p512c16-sqfull-m2-2 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -2 2824000 5067; run add5-p1024c16-v2full-m3-2 1024 "R=0.1,C16" "NN v2 + CRC search" -3 114500 5235; run add5-p1024c16-sqf-m1p5-0 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -1.5 1069000 5263 ) &   # ~2.9 h
( run add5-p512c16-sqfull-m2-3 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -2 2824000 5068; run add5-p1024c16-v2full-m3-3 1024 "R=0.1,C16" "NN v2 + CRC search" -3 114500 5236; run add5-p1024c16-sqf-m2-0 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -2 975500 5254 ) &   # ~2.9 h
( run add5-p512c16-sqfull-m2-4 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -2 2824000 5069; run add5-p1024c16-v2full-m3-4 1024 "R=0.1,C16" "NN v2 + CRC search" -3 114500 5237; run add5-p1024c16-sqf-m2p5-0 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -2.5 888500 5239 ) &   # ~2.9 h
( run add5-p512c16-sqfull-m2-5 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -2 2824000 5070; run add5-p1024c16-v2full-m3-5 1024 "R=0.1,C16" "NN v2 + CRC search" -3 114500 5238; run add5-p1024c16-sqf-m1-0 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -1 1064000 5274 ) &   # ~2.8 h
( run add5-p512c16-sqfull-m2-6 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -2 2824000 5071; run add5-p1024c16-sqfull-m2-0 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -2 186500 5255; run add5-p1024c16-sqfull-m3p5-1 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -3.5 119500 5218 ) &   # ~2.9 h
( run add5-p512c16-sqfull-m2-7 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -2 2824000 5072; run add5-p1024c16-sqfull-m2-1 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -2 186500 5256; run add5-p1024c16-sqfull-m3p5-2 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -3.5 119500 5219 ) &   # ~2.9 h
( run add5-p512c16-sqfull-m2-8 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -2 2824000 5073; run add5-p1024c16-sqfull-m2-2 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -2 186500 5257; run add5-p1024c16-sqf-m0p5-0 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search (first pass)" -0.5 1240500 5284 ) &   # ~2.9 h
( run add5-p512c16-sqfull-m2-9 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -2 2824000 5074; run add5-p1024c16-sqfull-m1p5-0 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1.5 234000 5264; run add5-p512c16-v2full-m2p5-2 512 "R=0.1,C16" "NN v2 + CRC search" -2.5 1649000 5051 ) &   # ~3.0 h
( run add5-p512c16-sqfull-m2-10 512 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -2 2824000 5075; run add5-p1024c16-sqfull-m1p5-1 1024 "R=0.1,C16" "Split pilots, quarter (ML) + CRC search" -1.5 234000 5265; run add5-p512c11-sqf-m0p5-0 512 "R=0.1" "Split pilots, quarter (ML) + CRC search (first pass)" -0.5 2584500 5013 ) &   # ~2.9 h
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
