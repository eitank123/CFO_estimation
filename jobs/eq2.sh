#!/bin/bash
# eq2: phase-equivariant receiver (no interleaver, BLIND_NOINT=1) vs the normal receiver (interleaver), same seed:
# same data / CFO / phase / noise (interleaving draws no random numbers), only the bit-to-symbol mapping differs (2026-11-13)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs small_cfo/blind/logs small_cfo/blind/results
R="$PY -u BLIND_IMPLEMENTATION/testing/run.py"
( $R --max-frames 4000 --seed 7804 --points 1/2:2:16 1/2:2.5:16 --rx base2_qfix --part t-eq2b
  BLIND_NOINT=1 $R --max-frames 4000 --seed 7804 --points 1/2:2:16 1/2:2.5:16 --rx base2_qfix_eq --part t-eq2e
  echo "ALL DONE" ) > logs/run_eq2.out 2>&1
