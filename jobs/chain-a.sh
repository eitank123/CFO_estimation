#!/bin/bash
# chain-a: 15 simulations from the add2 / lr12 / nn2 queue specs, commands verbatim.
# Lanes run side by side; inside a lane the simulations run one after another. A failure is logged
# and the lane goes on. Progress: logs/chain-a.progress ('done total elapsed_s'), log: logs/run_chain-a.out
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
LOG=logs/run_chain-a.out
PROG=logs/chain-a.progress
TOTAL=15
T0=$(date +%s)
mkdir -p logs lowrate/logs
: > "$PROG"
echo "$(date "+%F %T") chain start, $TOTAL simulations" > "$LOG"
finish() {  # name status
  echo "$(date "+%F %T") $2 $1" >> "$LOG"
  until mkdir "$PROG.lock" 2>/dev/null; do sleep 1; done   # portable lock: lanes finish independently
  echo $(( $(wc -l < "$PROG") + 1 )) $TOTAL $(( $(date +%s) - T0 )) >> "$PROG"
  rmdir "$PROG.lock"
}

sim_add2_p1024_nns_m2p5() {  # expected ~90 min
  echo "$(date "+%F %T") START add2-p1024-nns-m2p5" >> "$LOG"
  if CFO_STUDY=lowrate $PY -u polar_ber_experiment.py --mode ebn0 --packet 1024 --codes R=0.1,C16 --sources "SNR-aware NN + CRC search" --tag add2-p1024-nns-m2p5 --extra-esn0 -2.5 --max-frames 300000 --min-errors 100 --seed 2028 --workers 16 > lowrate/logs/run_add2-p1024-nns-m2p5.out 2>&1; then finish add2-p1024-nns-m2p5 DONE; else finish add2-p1024-nns-m2p5 "FAILED (exit $?, see lowrate/logs/run_add2-p1024-nns-m2p5.out)"; fi
}
sim_add2_p1024_nns_m2() {  # expected ~90 min
  echo "$(date "+%F %T") START add2-p1024-nns-m2" >> "$LOG"
  if CFO_STUDY=lowrate $PY -u polar_ber_experiment.py --mode ebn0 --packet 1024 --codes R=0.1,C16 --sources "SNR-aware NN + CRC search" --tag add2-p1024-nns-m2 --extra-esn0 -2 --max-frames 370000 --min-errors 100 --seed 2028 --workers 16 > lowrate/logs/run_add2-p1024-nns-m2.out 2>&1; then finish add2-p1024-nns-m2 DONE; else finish add2-p1024-nns-m2 "FAILED (exit $?, see lowrate/logs/run_add2-p1024-nns-m2.out)"; fi
}
sim_add2_p1024_nns_m1p5() {  # expected ~90 min
  echo "$(date "+%F %T") START add2-p1024-nns-m1p5" >> "$LOG"
  if CFO_STUDY=lowrate $PY -u polar_ber_experiment.py --mode ebn0 --packet 1024 --codes R=0.1,C16 --sources "SNR-aware NN + CRC search" --tag add2-p1024-nns-m1p5 --extra-esn0 -1.5 --max-frames 480000 --min-errors 100 --seed 2028 --workers 16 > lowrate/logs/run_add2-p1024-nns-m1p5.out 2>&1; then finish add2-p1024-nns-m1p5 DONE; else finish add2-p1024-nns-m1p5 "FAILED (exit $?, see lowrate/logs/run_add2-p1024-nns-m1p5.out)"; fi
}
sim_add2_p1024_nns_m1() {  # expected ~90 min
  echo "$(date "+%F %T") START add2-p1024-nns-m1" >> "$LOG"
  if CFO_STUDY=lowrate $PY -u polar_ber_experiment.py --mode ebn0 --packet 1024 --codes R=0.1,C16 --sources "SNR-aware NN + CRC search" --tag add2-p1024-nns-m1 --extra-esn0 -1 --max-frames 640000 --min-errors 100 --seed 2028 --workers 16 > lowrate/logs/run_add2-p1024-nns-m1.out 2>&1; then finish add2-p1024-nns-m1 DONE; else finish add2-p1024-nns-m1 "FAILED (exit $?, see lowrate/logs/run_add2-p1024-nns-m1.out)"; fi
}
sim_add2_p1024_nns_m0p5() {  # expected ~90 min
  echo "$(date "+%F %T") START add2-p1024-nns-m0p5" >> "$LOG"
  if CFO_STUDY=lowrate $PY -u polar_ber_experiment.py --mode ebn0 --packet 1024 --codes R=0.1,C16 --sources "SNR-aware NN + CRC search" --tag add2-p1024-nns-m0p5 --extra-esn0 -0.5 --max-frames 840000 --min-errors 100 --seed 2028 --workers 16 > lowrate/logs/run_add2-p1024-nns-m0p5.out 2>&1; then finish add2-p1024-nns-m0p5 DONE; else finish add2-p1024-nns-m0p5 "FAILED (exit $?, see lowrate/logs/run_add2-p1024-nns-m0p5.out)"; fi
}
sim_add2_p1024_nns_0() {  # expected ~90 min
  echo "$(date "+%F %T") START add2-p1024-nns-0" >> "$LOG"
  if CFO_STUDY=lowrate $PY -u polar_ber_experiment.py --mode ebn0 --packet 1024 --codes R=0.1,C16 --sources "SNR-aware NN + CRC search" --tag add2-p1024-nns-0 --extra-esn0 0 --max-frames 1100000 --min-errors 100 --seed 2028 --workers 16 > lowrate/logs/run_add2-p1024-nns-0.out 2>&1; then finish add2-p1024-nns-0 DONE; else finish add2-p1024-nns-0 "FAILED (exit $?, see lowrate/logs/run_add2-p1024-nns-0.out)"; fi
}
sim_add2_p1024_mms_m2p5() {  # expected ~90 min
  echo "$(date "+%F %T") START add2-p1024-mms-m2p5" >> "$LOG"
  if CFO_STUDY=lowrate $PY -u polar_ber_experiment.py --mode ebn0 --packet 1024 --codes R=0.1,C16 --sources "M&M + CRC search" --tag add2-p1024-mms-m2p5 --extra-esn0 -2.5 --max-frames 320000 --min-errors 100 --seed 2028 --workers 16 > lowrate/logs/run_add2-p1024-mms-m2p5.out 2>&1; then finish add2-p1024-mms-m2p5 DONE; else finish add2-p1024-mms-m2p5 "FAILED (exit $?, see lowrate/logs/run_add2-p1024-mms-m2p5.out)"; fi
}
sim_add2_p1024_mms_m2() {  # expected ~90 min
  echo "$(date "+%F %T") START add2-p1024-mms-m2" >> "$LOG"
  if CFO_STUDY=lowrate $PY -u polar_ber_experiment.py --mode ebn0 --packet 1024 --codes R=0.1,C16 --sources "M&M + CRC search" --tag add2-p1024-mms-m2 --extra-esn0 -2 --max-frames 400000 --min-errors 100 --seed 2028 --workers 16 > lowrate/logs/run_add2-p1024-mms-m2.out 2>&1; then finish add2-p1024-mms-m2 DONE; else finish add2-p1024-mms-m2 "FAILED (exit $?, see lowrate/logs/run_add2-p1024-mms-m2.out)"; fi
}
sim_add2_p1024_mms_m1p5() {  # expected ~90 min
  echo "$(date "+%F %T") START add2-p1024-mms-m1p5" >> "$LOG"
  if CFO_STUDY=lowrate $PY -u polar_ber_experiment.py --mode ebn0 --packet 1024 --codes R=0.1,C16 --sources "M&M + CRC search" --tag add2-p1024-mms-m1p5 --extra-esn0 -1.5 --max-frames 500000 --min-errors 100 --seed 2028 --workers 16 > lowrate/logs/run_add2-p1024-mms-m1p5.out 2>&1; then finish add2-p1024-mms-m1p5 DONE; else finish add2-p1024-mms-m1p5 "FAILED (exit $?, see lowrate/logs/run_add2-p1024-mms-m1p5.out)"; fi
}
sim_add2_p1024_mms_m1() {  # expected ~90 min
  echo "$(date "+%F %T") START add2-p1024-mms-m1" >> "$LOG"
  if CFO_STUDY=lowrate $PY -u polar_ber_experiment.py --mode ebn0 --packet 1024 --codes R=0.1,C16 --sources "M&M + CRC search" --tag add2-p1024-mms-m1 --extra-esn0 -1 --max-frames 700000 --min-errors 100 --seed 2028 --workers 16 > lowrate/logs/run_add2-p1024-mms-m1.out 2>&1; then finish add2-p1024-mms-m1 DONE; else finish add2-p1024-mms-m1 "FAILED (exit $?, see lowrate/logs/run_add2-p1024-mms-m1.out)"; fi
}
sim_add2_p1024_mms_m0p5() {  # expected ~90 min
  echo "$(date "+%F %T") START add2-p1024-mms-m0p5" >> "$LOG"
  if CFO_STUDY=lowrate $PY -u polar_ber_experiment.py --mode ebn0 --packet 1024 --codes R=0.1,C16 --sources "M&M + CRC search" --tag add2-p1024-mms-m0p5 --extra-esn0 -0.5 --max-frames 900000 --min-errors 100 --seed 2028 --workers 16 > lowrate/logs/run_add2-p1024-mms-m0p5.out 2>&1; then finish add2-p1024-mms-m0p5 DONE; else finish add2-p1024-mms-m0p5 "FAILED (exit $?, see lowrate/logs/run_add2-p1024-mms-m0p5.out)"; fi
}
sim_add2_p1024_mms_0() {  # expected ~90 min
  echo "$(date "+%F %T") START add2-p1024-mms-0" >> "$LOG"
  if CFO_STUDY=lowrate $PY -u polar_ber_experiment.py --mode ebn0 --packet 1024 --codes R=0.1,C16 --sources "M&M + CRC search" --tag add2-p1024-mms-0 --extra-esn0 0 --max-frames 1200000 --min-errors 100 --seed 2028 --workers 16 > lowrate/logs/run_add2-p1024-mms-0.out 2>&1; then finish add2-p1024-mms-0 DONE; else finish add2-p1024-mms-0 "FAILED (exit $?, see lowrate/logs/run_add2-p1024-mms-0.out)"; fi
}
sim_lr12_r01c16_mms_a() {  # expected ~6 min
  echo "$(date "+%F %T") START lr12-r01c16-mms-a" >> "$LOG"
  if CFO_STUDY=lowrate $PY -u polar_ber_experiment.py --mode ebn0 --codes R=0.1,C16 --sources "M&M + CRC search" --tag lr12-r01c16-mms-a --extra-esn0 -5 -4.5 -4 -3.5 --max-frames 1000000 --min-errors 300 --workers 16 > lowrate/logs/run_lr12-r01c16-mms-a.out 2>&1; then finish lr12-r01c16-mms-a DONE; else finish lr12-r01c16-mms-a "FAILED (exit $?, see lowrate/logs/run_lr12-r01c16-mms-a.out)"; fi
}
sim_lr12_r01c16_mms_b() {  # expected ~27 min
  echo "$(date "+%F %T") START lr12-r01c16-mms-b" >> "$LOG"
  if CFO_STUDY=lowrate $PY -u polar_ber_experiment.py --mode ebn0 --codes R=0.1,C16 --sources "M&M + CRC search" --tag lr12-r01c16-mms-b --extra-esn0 -3 -2.5 -2 -1.5 --max-frames 1000000 --min-errors 300 --workers 16 > lowrate/logs/run_lr12-r01c16-mms-b.out 2>&1; then finish lr12-r01c16-mms-b DONE; else finish lr12-r01c16-mms-b "FAILED (exit $?, see lowrate/logs/run_lr12-r01c16-mms-b.out)"; fi
}
sim_lr12_r01c16_mms_c() {  # expected ~21 min
  echo "$(date "+%F %T") START lr12-r01c16-mms-c" >> "$LOG"
  if CFO_STUDY=lowrate $PY -u polar_ber_experiment.py --mode ebn0 --codes R=0.1,C16 --sources "M&M + CRC search" --tag lr12-r01c16-mms-c --extra-esn0 -1 -0.5 0 --max-frames 1000000 --min-errors 300 --workers 16 > lowrate/logs/run_lr12-r01c16-mms-c.out 2>&1; then finish lr12-r01c16-mms-c DONE; else finish lr12-r01c16-mms-c "FAILED (exit $?, see lowrate/logs/run_lr12-r01c16-mms-c.out)"; fi
}

( sim_add2_p1024_nns_m2p5 ) &   # lane 1: ~90 min
( sim_add2_p1024_nns_m2 ) &   # lane 2: ~90 min
( sim_add2_p1024_nns_m1p5 ) &   # lane 3: ~90 min
( sim_add2_p1024_nns_m1 ) &   # lane 4: ~90 min
( sim_add2_p1024_nns_m0p5 ) &   # lane 5: ~90 min
( sim_add2_p1024_nns_0 ) &   # lane 6: ~90 min
( sim_add2_p1024_mms_m2p5 ) &   # lane 7: ~90 min
( sim_add2_p1024_mms_m2 ) &   # lane 8: ~90 min
( sim_add2_p1024_mms_m1p5 ) &   # lane 9: ~90 min
( sim_add2_p1024_mms_m1 ) &   # lane 10: ~90 min
( sim_add2_p1024_mms_m0p5 ) &   # lane 11: ~90 min
( sim_add2_p1024_mms_0 ) &   # lane 12: ~90 min
( sim_lr12_r01c16_mms_a; sim_lr12_r01c16_mms_b; sim_lr12_r01c16_mms_c ) &   # lane 13: ~54 min
wait
echo "EVAL DONE: all $TOTAL simulations finished ($(grep -c FAILED "$LOG") failed)" >> "$LOG"
