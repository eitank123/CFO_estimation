#!/bin/bash
# fs-rechg: fullsys/recharge.py, offline upper bound on the checkpoint NN's uncharged MACs of the FINAL parts (no
# simulation: builds the formats' codes for m_met / sh0, reads the JSONs and dumps); exact values = the fs-q* reruns
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
(
  $PY -u fullsys/recharge.py fs-g13m08 fs-g13m06 fs-g13m04 fs-g13m02 fs-g13p00 fs-h13m06 fs-g42m42 fs-g42m40 fs-g42m38 fs-g42m36 fs-g42m34 fs-g42m32 fs-g42m30 fs-h42m38 fs-h42m36 fs-g3m10 fs-g3m08 fs-g3m06 fs-g3m04 fs-g3m02 fs-g3p00 fs-g3p02 fs-g3p04 fs-g3p06 fs-g3p08 fs-g3p10 fs-g14p10 fs-g14p12 fs-g14p14 fs-g14p16 fs-g14p18 fs-g14p20 fs-g14p22 fs-h14p18
  echo "ALL DONE" ) > logs/run_fs-rechg.out 2>&1
