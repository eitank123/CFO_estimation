#!/bin/bash
# fs-dasmoke2: smoke test of the reworked DA runner (costmodel sync costs, per-error rows, standard_* from attempt 1,
# --check), 100 frames per point at high-PER points, every path. Checks (CHECK PASSED / FAILED lines):
#   13s (--n0 est) == 13n (--n0 genie): max-log decoding is invariant to the per-packet LLR scale
#   rcs2 ideal 13i == run_rcs2 ref, vde ideal v32i == run_vde vref (chunk_err vs chunks.err_idx): exact pairing
# fs-dasmoke (the old code) used other part names. Memory: 32Gi.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
R="$PY -u fullsys/run_fullsys_da.py --frames 100 --max-err 100 --seed 900 --workers 16"
D=fullsys/results
( $PY -u fullsys/run_fullsys_da.py --selfcheck
  $R --sys rcs2 --wf 13 --snrs -1.20 --variant strong --dump --part fs-dasmoke2-13t
  $R --sys rcs2 --wf 13 --snrs -1.20 --variant standard --part fs-dasmoke2-13s
  $R --sys rcs2 --wf 13 --snrs -1.20 --variant standard --n0 genie --part fs-dasmoke2-13n
  $PY -u fullsys/run_fullsys_da.py --check $D/da_fs-dasmoke2-13s.json $D/da_fs-dasmoke2-13n.json
  $R --sys rcs2 --wf 13 --snrs -1.20 --variant genie --part fs-dasmoke2-13g
  $R --sys rcs2 --wf 13 --snrs -1.20 --variant ideal --part fs-dasmoke2-13i
  $PY -u fullsys/run_rcs2.py --wf 13 --snrs -1.20 --frames 100 --max-err 100 --seed 900 --workers 16 --part fs-dasmoke2-ref
  $PY -u fullsys/run_fullsys_da.py --check $D/rcs2_fs-dasmoke2-ref.json $D/da_fs-dasmoke2-13i.json
  $R --sys rcs2 --wf 13 --snrs -1.20 --variant standard --dd-iters 2 --part fs-dasmoke2-13d
  $R --sys rcs2 --wf 13 --snrs -1.20 --variant strong --cfo-max 0.005 --part fs-dasmoke2-13w
  $R --sys rcs2 --wf 13 --snrs -1.20 --variant strong --calib-seed-offset 1000000 --part fs-dasmoke2-13c
  $R --sys rcs2 --wf 3 --snrs -0.67 --variant strong --part fs-dasmoke2-3t
  $R --sys rcs2 --wf 14 --snrs 1.09 --variant strong --part fs-dasmoke2-14t
  $R --sys rcs2 --wf 42 --snrs -4.21 --variant strong --part fs-dasmoke2-42t
  $R --sys vde --link 32 --snrs -5.0 --variant strong --algo logmap --dump --part fs-dasmoke2-v32t
  $R --sys vde --link 32 --snrs -5.0 --variant genie --algo logmap --part fs-dasmoke2-v32g
  $R --sys vde --link 32 --snrs -5.0 --variant ideal --algo logmap --part fs-dasmoke2-v32i
  $PY -u fullsys/run_vde.py --link 32 --snrs -5.0 --frames 100 --max-err 100 --seed 900 --workers 16 --algo logmap --part fs-dasmoke2-vref
  $PY -u fullsys/run_fullsys_da.py --check $D/vde_fs-dasmoke2-vref.json $D/da_fs-dasmoke2-v32i.json
  echo "ALL DONE" ) > logs/run_fs-dasmoke2.out 2>&1
