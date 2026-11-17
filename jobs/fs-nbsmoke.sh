#!/bin/bash
# fs-nbsmoke: smoke test of the NB-IoT NPUSCH F1 competitor (fullsys/nbiot.py, turbo_lte.py, run_fullsys_da --sys nbiot,
# run_polar_genie nb* formats): self-tests, then 100 frames per run at a high-PER point of every format and every path
# (strong / standard / n0 genie / genie / ideal, +-0.035 and +-0.055, log-MAP, the code-only AFF3CT format, polar genie).
# Checks (CHECK PASSED / FAILED lines): 328s (--n0 est) == 328n (--n0 genie) (max-log turbo is invariant to the
# per-packet LLR scale). The smoke SNRs are first guesses: read the PER per format before fixing the fs-nbv grids.
# Also prints whether sionna.phy.fec.turbo imports in the env (info only; turbo_lte.py does not use it). Memory: 32Gi.
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
R="$PY -u fullsys/run_fullsys_da.py --sys nbiot --frames 100 --max-err 100 --seed 900 --workers 16"
D=fullsys/results
( $PY -u fullsys/selftest_nbiot.py
  $PY -u fullsys/run_fullsys_da.py --selfcheck
  $PY -u fullsys/run_polar_genie.py --selfcheck
  $PY -c "import sionna, importlib; m = importlib.import_module(\"sionna.phy.fec.turbo\"); print(\"sionna\", sionna.__version__, \"turbo importable\", m.TurboEncoder)" || echo "sionna turbo NOT importable (info only)"
  $R --nbfmt nb328 --snrs -1.50 --variant strong --cfo-max 0.035 --dump --part fs-nbsmoke-328t
  $R --nbfmt nb328 --snrs -1.50 --variant standard --cfo-max 0.035 --part fs-nbsmoke-328s
  $R --nbfmt nb328 --snrs -1.50 --variant standard --cfo-max 0.035 --n0 genie --part fs-nbsmoke-328n
  $PY -u fullsys/run_fullsys_da.py --check $D/da_fs-nbsmoke-328s.json $D/da_fs-nbsmoke-328n.json
  $R --nbfmt nb328 --snrs -1.50 --variant genie --cfo-max 0.035 --part fs-nbsmoke-328g
  $R --nbfmt nb328 --snrs -1.50 --variant ideal --part fs-nbsmoke-328i
  $R --nbfmt nb328 --snrs -1.50 --variant strong --cfo-max 0.055 --part fs-nbsmoke-328w
  $R --nbfmt nb328 --snrs -1.50 --variant strong --cfo-max 0.035 --algo logmap --part fs-nbsmoke-328l
  $R --nbfmt nb208 --snrs -3.30 --variant strong --cfo-max 0.035 --part fs-nbsmoke-208t
  $R --nbfmt nb208b --snrs -4.50 --variant strong --cfo-max 0.035 --part fs-nbsmoke-208b
  $R --nbfmt nb296 --snrs 5.50 --variant strong --cfo-max 0.035 --part fs-nbsmoke-296t
  $R --nbfmt nb808 --snrs 1.50 --variant strong --cfo-max 0.035 --part fs-nbsmoke-808t
  $R --nbfmt nb1000 --snrs 3.00 --variant strong --cfo-max 0.035 --part fs-nbsmoke-1000t
  $R --nbfmt nb1000r10 --snrs 1.50 --variant strong --cfo-max 0.055 --part fs-nbsmoke-1000r
  $R --nbfmt aff3ct-K2048 --snrs -2.07 --variant ideal --frames 400 --part fs-nbsmoke-aff
  $PY -u fullsys/run_polar_genie.py --fmt nb328 --snrs -1.50 --frames 200 --max-err 100 --seed 900 --workers 16 --part fs-nbsmoke-pg328
  $PY -u fullsys/run_polar_genie.py --fmt nb208b --snrs -4.50 --frames 200 --max-err 100 --seed 900 --workers 16 --part fs-nbsmoke-pg208b
  echo "ALL DONE" ) > logs/run_fs-nbsmoke.out 2>&1
