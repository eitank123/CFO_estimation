#!/bin/bash
# p64r10-a: 64-symbol preamble BLER (r10), lowrate study, 1024 symbols, est-len 64; one chunk per lane
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg CFO_STUDY=lowrate
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_p64r10-a.out
PROG=logs/p64r10-a.progress
TOTAL=70
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

( run addp64r10-mmf-0p0-0 "R=0.1,C16" "M&M + CRC search (first pass)" 0.0 300000 64000; run addp64r10-mmf-m1p0-0 "R=0.1,C16" "M&M + CRC search (first pass)" -1.0 300000 64016; run addp64r10-mmf-m2p5-0 "R=0.1,C16" "M&M + CRC search (first pass)" -2.5 300000 64032; run addp64r10-genie-0p0-0 "R=0.1,C16" "Genie (known CFO)" 0.0 300000 64048; run addp64r10-genie-m4p0-0 "R=0.1,C16" "Genie (known CFO)" -4.0 300000 64064 ) &
( run addp64r10-mmf-0p0-1 "R=0.1,C16" "M&M + CRC search (first pass)" 0.0 300000 64001; run addp64r10-mmf-m1p0-1 "R=0.1,C16" "M&M + CRC search (first pass)" -1.0 300000 64017; run addp64r10-mmf-m2p5-1 "R=0.1,C16" "M&M + CRC search (first pass)" -2.5 300000 64033; run addp64r10-mm-0p0-0 "R=0.1,C16" "M&M" 0.0 300000 64049; run addp64r10-mm-m4p0-0 "R=0.1,C16" "M&M" -4.0 300000 64065 ) &
( run addp64r10-mmf-0p0-2 "R=0.1,C16" "M&M + CRC search (first pass)" 0.0 300000 64002; run addp64r10-mmf-m1p0-2 "R=0.1,C16" "M&M + CRC search (first pass)" -1.0 300000 64018; run addp64r10-nnf-m2p5-0 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" -2.5 300000 64034; run addp64r10-genie-m0p5-0 "R=0.1,C16" "Genie (known CFO)" -0.5 300000 64050; run addp64r10-genie-m4p5-0 "R=0.1,C16" "Genie (known CFO)" -4.5 300000 64066 ) &
( run addp64r10-mmf-0p0-3 "R=0.1,C16" "M&M + CRC search (first pass)" 0.0 300000 64003; run addp64r10-mmf-m1p0-3 "R=0.1,C16" "M&M + CRC search (first pass)" -1.0 300000 64019; run addp64r10-nnf-m2p5-1 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" -2.5 300000 64035; run addp64r10-mm-m0p5-0 "R=0.1,C16" "M&M" -0.5 300000 64051; run addp64r10-mm-m4p5-0 "R=0.1,C16" "M&M" -4.5 300000 64067 ) &
( run addp64r10-nnf-0p0-0 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" 0.0 300000 64004; run addp64r10-nnf-m1p0-0 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" -1.0 300000 64020; run addp64r10-mmf-m3p0-0 "R=0.1,C16" "M&M + CRC search (first pass)" -3.0 300000 64036; run addp64r10-genie-m1p0-0 "R=0.1,C16" "Genie (known CFO)" -1.0 300000 64052; run addp64r10-genie-m5p0-0 "R=0.1,C16" "Genie (known CFO)" -5.0 300000 64068 ) &
( run addp64r10-nnf-0p0-1 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" 0.0 300000 64005; run addp64r10-nnf-m1p0-1 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" -1.0 300000 64021; run addp64r10-mmf-m3p0-1 "R=0.1,C16" "M&M + CRC search (first pass)" -3.0 300000 64037; run addp64r10-mm-m1p0-0 "R=0.1,C16" "M&M" -1.0 300000 64053; run addp64r10-mm-m5p0-0 "R=0.1,C16" "M&M" -5.0 300000 64069 ) &
( run addp64r10-nnf-0p0-2 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" 0.0 300000 64006; run addp64r10-nnf-m1p0-2 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" -1.0 300000 64022; run addp64r10-nnf-m3p0-0 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" -3.0 300000 64038; run addp64r10-genie-m1p5-0 "R=0.1,C16" "Genie (known CFO)" -1.5 300000 64054 ) &
( run addp64r10-nnf-0p0-3 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" 0.0 300000 64007; run addp64r10-nnf-m1p0-3 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" -1.0 300000 64023; run addp64r10-nnf-m3p0-1 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" -3.0 300000 64039; run addp64r10-mm-m1p5-0 "R=0.1,C16" "M&M" -1.5 300000 64055 ) &
( run addp64r10-mmf-m0p5-0 "R=0.1,C16" "M&M + CRC search (first pass)" -0.5 300000 64008; run addp64r10-mmf-m1p5-0 "R=0.1,C16" "M&M + CRC search (first pass)" -1.5 300000 64024; run addp64r10-mmf-m3p5-0 "R=0.1,C16" "M&M + CRC search (first pass)" -3.5 300000 64040; run addp64r10-genie-m2p0-0 "R=0.1,C16" "Genie (known CFO)" -2.0 300000 64056 ) &
( run addp64r10-mmf-m0p5-1 "R=0.1,C16" "M&M + CRC search (first pass)" -0.5 300000 64009; run addp64r10-mmf-m1p5-1 "R=0.1,C16" "M&M + CRC search (first pass)" -1.5 300000 64025; run addp64r10-nnf-m3p5-0 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" -3.5 300000 64041; run addp64r10-mm-m2p0-0 "R=0.1,C16" "M&M" -2.0 300000 64057 ) &
( run addp64r10-mmf-m0p5-2 "R=0.1,C16" "M&M + CRC search (first pass)" -0.5 300000 64010; run addp64r10-nnf-m1p5-0 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" -1.5 300000 64026; run addp64r10-mmf-m4p0-0 "R=0.1,C16" "M&M + CRC search (first pass)" -4.0 300000 64042; run addp64r10-genie-m2p5-0 "R=0.1,C16" "Genie (known CFO)" -2.5 300000 64058 ) &
( run addp64r10-mmf-m0p5-3 "R=0.1,C16" "M&M + CRC search (first pass)" -0.5 300000 64011; run addp64r10-nnf-m1p5-1 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" -1.5 300000 64027; run addp64r10-nnf-m4p0-0 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" -4.0 300000 64043; run addp64r10-mm-m2p5-0 "R=0.1,C16" "M&M" -2.5 300000 64059 ) &
( run addp64r10-nnf-m0p5-0 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" -0.5 300000 64012; run addp64r10-mmf-m2p0-0 "R=0.1,C16" "M&M + CRC search (first pass)" -2.0 300000 64028; run addp64r10-mmf-m4p5-0 "R=0.1,C16" "M&M + CRC search (first pass)" -4.5 300000 64044; run addp64r10-genie-m3p0-0 "R=0.1,C16" "Genie (known CFO)" -3.0 300000 64060 ) &
( run addp64r10-nnf-m0p5-1 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" -0.5 300000 64013; run addp64r10-mmf-m2p0-1 "R=0.1,C16" "M&M + CRC search (first pass)" -2.0 300000 64029; run addp64r10-nnf-m4p5-0 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" -4.5 300000 64045; run addp64r10-mm-m3p0-0 "R=0.1,C16" "M&M" -3.0 300000 64061 ) &
( run addp64r10-nnf-m0p5-2 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" -0.5 300000 64014; run addp64r10-nnf-m2p0-0 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" -2.0 300000 64030; run addp64r10-mmf-m5p0-0 "R=0.1,C16" "M&M + CRC search (first pass)" -5.0 300000 64046; run addp64r10-genie-m3p5-0 "R=0.1,C16" "Genie (known CFO)" -3.5 300000 64062 ) &
( run addp64r10-nnf-m0p5-3 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" -0.5 300000 64015; run addp64r10-nnf-m2p0-1 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" -2.0 300000 64031; run addp64r10-nnf-m5p0-0 "R=0.1,C16" "SNR-aware NN + CRC search (first pass)" -5.0 300000 64047; run addp64r10-mm-m3p5-0 "R=0.1,C16" "M&M" -3.5 300000 64063 ) &
wait
echo "EVAL DONE: all $TOTAL chunks finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
