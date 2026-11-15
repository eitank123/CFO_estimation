#!/bin/bash
# p64r4-a: 64-symbol preamble BLER (r4), lowrate study, 1024 symbols, est-len 64; one chunk per lane
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_p64r4-a.out
PROG=logs/p64r4-a.progress
TOTAL=55
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

( run addp64r4-mmf-10p0-0 "R=1/4,C16" "M&M + CRC search (first pass)" 10.0 300000 65000; run addp64r4-mmf-5p0-2 "R=1/4,C16" "M&M + CRC search (first pass)" 5.0 300000 65032; run addp64r4-nnf-1p5-1 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 1.5 300000 65064; run addp64r4-mm-4p0-0 "R=1/4,C16" "M&M" 4.0 300000 65096 ) &
( run addp64r4-mmf-10p0-2 "R=1/4,C16" "M&M + CRC search (first pass)" 10.0 300000 65002; run addp64r4-nnf-5p0-1 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 5.0 300000 65034; run addp64r4-mmf-1p0-0 "R=1/4,C16" "M&M + CRC search (first pass)" 1.0 300000 65066; run addp64r4-mm-2p5-0 "R=1/4,C16" "M&M" 2.5 300000 65098 ) &
( run addp64r4-nnf-10p0-1 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 10.0 300000 65004; run addp64r4-mmf-4p0-0 "R=1/4,C16" "M&M + CRC search (first pass)" 4.0 300000 65036; run addp64r4-mmf-1p0-2 "R=1/4,C16" "M&M + CRC search (first pass)" 1.0 300000 65068; run addp64r4-mm-1p5-0 "R=1/4,C16" "M&M" 1.5 300000 65100 ) &
( run addp64r4-mmf-9p0-0 "R=1/4,C16" "M&M + CRC search (first pass)" 9.0 300000 65006; run addp64r4-mmf-4p0-2 "R=1/4,C16" "M&M + CRC search (first pass)" 4.0 300000 65038; run addp64r4-nnf-1p0-1 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 1.0 300000 65070; run addp64r4-genie-1p0-1 "R=1/4,C16" "Genie (known CFO)" 1.0 300000 65102 ) &
( run addp64r4-mmf-9p0-2 "R=1/4,C16" "M&M + CRC search (first pass)" 9.0 300000 65008; run addp64r4-nnf-4p0-1 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 4.0 300000 65040; run addp64r4-mmf-0p5-0 "R=1/4,C16" "M&M + CRC search (first pass)" 0.5 300000 65072; run addp64r4-genie-0p5-0 "R=1/4,C16" "Genie (known CFO)" 0.5 300000 65104 ) &
( run addp64r4-nnf-9p0-1 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 9.0 300000 65010; run addp64r4-mmf-3p0-0 "R=1/4,C16" "M&M + CRC search (first pass)" 3.0 300000 65042; run addp64r4-nnf-0p5-0 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 0.5 300000 65074; run addp64r4-mm-0p5-0 "R=1/4,C16" "M&M" 0.5 300000 65106 ) &
( run addp64r4-mmf-8p0-0 "R=1/4,C16" "M&M + CRC search (first pass)" 8.0 300000 65012; run addp64r4-mmf-3p0-2 "R=1/4,C16" "M&M + CRC search (first pass)" 3.0 300000 65044; run addp64r4-mmf-0p0-0 "R=1/4,C16" "M&M + CRC search (first pass)" 0.0 300000 65076; run addp64r4-genie-0p0-1 "R=1/4,C16" "Genie (known CFO)" 0.0 300000 65108 ) &
( run addp64r4-mmf-8p0-2 "R=1/4,C16" "M&M + CRC search (first pass)" 8.0 300000 65014; run addp64r4-nnf-3p0-1 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 3.0 300000 65046; run addp64r4-nnf-0p0-0 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 0.0 300000 65078 ) &
( run addp64r4-nnf-8p0-1 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 8.0 300000 65016; run addp64r4-mmf-2p5-0 "R=1/4,C16" "M&M + CRC search (first pass)" 2.5 300000 65048; run addp64r4-mm-10p0-0 "R=1/4,C16" "M&M" 10.0 300000 65080 ) &
( run addp64r4-mmf-7p0-0 "R=1/4,C16" "M&M + CRC search (first pass)" 7.0 300000 65018; run addp64r4-mmf-2p5-2 "R=1/4,C16" "M&M + CRC search (first pass)" 2.5 300000 65050; run addp64r4-mm-10p0-2 "R=1/4,C16" "M&M" 10.0 300000 65082 ) &
( run addp64r4-mmf-7p0-2 "R=1/4,C16" "M&M + CRC search (first pass)" 7.0 300000 65020; run addp64r4-nnf-2p5-1 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 2.5 300000 65052; run addp64r4-mm-9p0-1 "R=1/4,C16" "M&M" 9.0 300000 65084 ) &
( run addp64r4-nnf-7p0-1 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 7.0 300000 65022; run addp64r4-mmf-2p0-0 "R=1/4,C16" "M&M + CRC search (first pass)" 2.0 300000 65054; run addp64r4-mm-8p0-0 "R=1/4,C16" "M&M" 8.0 300000 65086 ) &
( run addp64r4-mmf-6p0-0 "R=1/4,C16" "M&M + CRC search (first pass)" 6.0 300000 65024; run addp64r4-mmf-2p0-2 "R=1/4,C16" "M&M + CRC search (first pass)" 2.0 300000 65056; run addp64r4-mm-8p0-2 "R=1/4,C16" "M&M" 8.0 300000 65088 ) &
( run addp64r4-mmf-6p0-2 "R=1/4,C16" "M&M + CRC search (first pass)" 6.0 300000 65026; run addp64r4-nnf-2p0-1 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 2.0 300000 65058; run addp64r4-mm-7p0-1 "R=1/4,C16" "M&M" 7.0 300000 65090 ) &
( run addp64r4-nnf-6p0-1 "R=1/4,C16" "SNR-aware NN + CRC search (first pass)" 6.0 300000 65028; run addp64r4-mmf-1p5-0 "R=1/4,C16" "M&M + CRC search (first pass)" 1.5 300000 65060; run addp64r4-mm-6p0-0 "R=1/4,C16" "M&M" 6.0 300000 65092 ) &
( run addp64r4-mmf-5p0-0 "R=1/4,C16" "M&M + CRC search (first pass)" 5.0 300000 65030; run addp64r4-mmf-1p5-2 "R=1/4,C16" "M&M + CRC search (first pass)" 1.5 300000 65062; run addp64r4-mm-6p0-2 "R=1/4,C16" "M&M" 6.0 300000 65094 ) &
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
