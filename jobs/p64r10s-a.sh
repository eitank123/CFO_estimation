#!/bin/bash
# p64r10s-a: 64-symbol preamble BLER (r10snn), lowrate study, 1024 symbols, est-len 64; one chunk per lane
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_p64r10s-a.out
PROG=logs/p64r10s-a.progress
TOTAL=35
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
run() {  # tag code source esn0 frames seed
  if $PY -u polar_ber_experiment.py --mode ebn0 --packet 1024 --est-len 64 --codes "$2" --sources "$3" --tag $1 --extra-esn0 $4 --min-errors 100 --max-frames $5 --seed $6 --workers 1 > lowrate/logs/run_$1.out 2>&1; then finish $1 DONE; else finish $1 "FAILED (exit $?)"; fi
}

( run addp64r10s-snnf-0p0-0 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" 0.0 300000 66000; run addp64r10s-snnf-m2p5-0 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -2.5 300000 66016; run addp64r10s-snn-m4p0-0 "R=0.1,C16" "Split pilots NN, quarter" -4.0 300000 66032 ) &
( run addp64r10s-snnf-0p0-1 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" 0.0 300000 66001; run addp64r10s-snnf-m2p5-1 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -2.5 300000 66017; run addp64r10s-snn-m4p5-0 "R=0.1,C16" "Split pilots NN, quarter" -4.5 300000 66033 ) &
( run addp64r10s-snnf-0p0-2 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" 0.0 300000 66002; run addp64r10s-snnf-m3p0-0 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -3.0 300000 66018; run addp64r10s-snn-m5p0-0 "R=0.1,C16" "Split pilots NN, quarter" -5.0 300000 66034 ) &
( run addp64r10s-snnf-0p0-3 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" 0.0 300000 66003; run addp64r10s-snnf-m3p0-1 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -3.0 300000 66019 ) &
( run addp64r10s-snnf-m0p5-0 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -0.5 300000 66004; run addp64r10s-snnf-m3p5-0 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -3.5 300000 66020 ) &
( run addp64r10s-snnf-m0p5-1 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -0.5 300000 66005; run addp64r10s-snnf-m4p0-0 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -4.0 300000 66021 ) &
( run addp64r10s-snnf-m0p5-2 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -0.5 300000 66006; run addp64r10s-snnf-m4p5-0 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -4.5 300000 66022 ) &
( run addp64r10s-snnf-m0p5-3 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -0.5 300000 66007; run addp64r10s-snnf-m5p0-0 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -5.0 300000 66023 ) &
( run addp64r10s-snnf-m1p0-0 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -1.0 300000 66008; run addp64r10s-snn-0p0-0 "R=0.1,C16" "Split pilots NN, quarter" 0.0 300000 66024 ) &
( run addp64r10s-snnf-m1p0-1 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -1.0 300000 66009; run addp64r10s-snn-m0p5-0 "R=0.1,C16" "Split pilots NN, quarter" -0.5 300000 66025 ) &
( run addp64r10s-snnf-m1p0-2 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -1.0 300000 66010; run addp64r10s-snn-m1p0-0 "R=0.1,C16" "Split pilots NN, quarter" -1.0 300000 66026 ) &
( run addp64r10s-snnf-m1p0-3 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -1.0 300000 66011; run addp64r10s-snn-m1p5-0 "R=0.1,C16" "Split pilots NN, quarter" -1.5 300000 66027 ) &
( run addp64r10s-snnf-m1p5-0 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -1.5 300000 66012; run addp64r10s-snn-m2p0-0 "R=0.1,C16" "Split pilots NN, quarter" -2.0 300000 66028 ) &
( run addp64r10s-snnf-m1p5-1 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -1.5 300000 66013; run addp64r10s-snn-m2p5-0 "R=0.1,C16" "Split pilots NN, quarter" -2.5 300000 66029 ) &
( run addp64r10s-snnf-m2p0-0 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -2.0 300000 66014; run addp64r10s-snn-m3p0-0 "R=0.1,C16" "Split pilots NN, quarter" -3.0 300000 66030 ) &
( run addp64r10s-snnf-m2p0-1 "R=0.1,C16" "Split pilots NN, quarter + CRC search (first pass)" -2.0 300000 66015; run addp64r10s-snn-m3p5-0 "R=0.1,C16" "Split pilots NN, quarter" -3.5 300000 66031 ) &
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
