#!/bin/bash
# fs-dasmoke: smoke test of the DA synchroniser runner (fullsys/run_fullsys_da.py), 100 frames per point at high-PER
# points, every path: selfcheck; RCS2 13 standard / strong (+ dump) / genie / ideal / --n0 genie / --dd-iters 2;
# strong on 3, 14, 42; VDE 32 standard / strong (+ dump) / genie / ideal. Pairing check: 'ideal' must reproduce
# run_rcs2 / run_vde bit-exactly (same seed 900: equal frame_err and chunks.err_idx in rcs2_fs-dasmoke-ref.json vs
# da_fs-dasmoke-13i.json, vde_fs-dasmoke-vref.json frame_err vs da_fs-dasmoke-v32i.json). Memory: 32Gi.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
R="$PY -u fullsys/run_fullsys_da.py --frames 100 --max-err 100 --seed 900 --workers 16"
( $PY -u fullsys/run_fullsys_da.py --selfcheck
  $R --sys rcs2 --wf 13 --snrs -1.20 --variant standard --part fs-dasmoke-13s
  $R --sys rcs2 --wf 13 --snrs -1.20 --variant strong --dump --part fs-dasmoke-13t
  $R --sys rcs2 --wf 13 --snrs -1.20 --variant genie --part fs-dasmoke-13g
  $R --sys rcs2 --wf 13 --snrs -1.20 --variant ideal --part fs-dasmoke-13i
  $R --sys rcs2 --wf 13 --snrs -1.20 --variant standard --n0 genie --part fs-dasmoke-13n
  $R --sys rcs2 --wf 13 --snrs -1.20 --variant standard --dd-iters 2 --part fs-dasmoke-13d
  $R --sys rcs2 --wf 3 --snrs -0.67 --variant strong --part fs-dasmoke-3t
  $R --sys rcs2 --wf 14 --snrs 1.09 --variant strong --part fs-dasmoke-14t
  $R --sys rcs2 --wf 42 --snrs -4.21 --variant strong --part fs-dasmoke-42t
  $PY -u fullsys/run_rcs2.py --wf 13 --snrs -1.20 --frames 100 --max-err 100 --seed 900 --workers 16 --part fs-dasmoke-ref
  $R --sys vde --link 32 --snrs -5.0 --variant standard --algo logmap --part fs-dasmoke-v32s
  $R --sys vde --link 32 --snrs -5.0 --variant strong --algo logmap --dump --part fs-dasmoke-v32t
  $R --sys vde --link 32 --snrs -5.0 --variant genie --algo logmap --part fs-dasmoke-v32g
  $R --sys vde --link 32 --snrs -5.0 --variant ideal --algo logmap --part fs-dasmoke-v32i
  $PY -u fullsys/run_vde.py --link 32 --snrs -5.0 --frames 100 --max-err 100 --seed 900 --workers 16 --algo logmap --part fs-dasmoke-vref
  echo "ALL DONE" ) > logs/run_fs-dasmoke.out 2>&1
