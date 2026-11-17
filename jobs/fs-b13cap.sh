#!/bin/bash
# fs-b13cap: SMOKE of --cap-core on ID 13 (GA design, channel interleaver on, CFO U(+-0.03)), Es/N0 -0.6 and -0.2, 300 packets each, seed 1313 batch 20, --dump: the SAME packets without a cap (fs-b13cap-nc) and with --cap-core 5e6 (fs-b13cap-c5), then fullsys/cmp_cap.py (requirement: the 5M cap costs no packet)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg BLIND_STUDY=small_cfo
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( $PY -u fullsys/run_blind_fs.py --fmt id13 --design ga --snrs -0.6 -0.2 --frames 300 --max-err 300 --batch 20 --sub 20 --seed 1313 --cfo-max 0.03 --workers 16 --dump --part fs-b13cap-nc
  $PY -u fullsys/run_blind_fs.py --fmt id13 --design ga --snrs -0.6 -0.2 --frames 300 --max-err 300 --batch 20 --sub 20 --seed 1313 --cfo-max 0.03 --workers 16 --dump --cap-core 5e6 --part fs-b13cap-c5
  $PY -u fullsys/cmp_cap.py fullsys/results/blind_fs_fs-b13cap-nc.json fullsys/results/blind_fs_fs-b13cap-c5.json
  echo "ALL DONE" ) > logs/run_fs-b13cap.out 2>&1
