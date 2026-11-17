#!/bin/bash
# fs-aff3ctsmoke: toolchain check for the AFF3CT build (fs-aff3ct): compilers, cmake, make, nproc, pip of the env, network for pip
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( echo "host $(hostname)  nproc $(nproc)  date $(date)"
  head -2 /etc/os-release 2>/dev/null; ldd --version 2>&1 | head -1
  echo "which: $(which cmake g++ gcc make c++ 2>&1 | tr '\n' ' ')"
  for t in cmake g++ gcc make c++ cc clang++ ninja tar; do
    p=$(command -v $t)
    if [ -n "$p" ]; then echo "== $t: $p | $($t --version 2>&1 | head -1)"; else echo "== $t: MISSING"; fi
  done
  echo "== env compilers: $(ls $(dirname $PY) | grep -E 'g\+\+|gcc|clang|cmake|ninja' | tr '\n' ' ')"
  $PY -m pip --version; echo "pip exit $?"
  $PY -m pip show cmake ninja 2>&1 | grep -E '^(Name|Version)'
  timeout 90 $PY -m pip download --no-deps --only-binary :all: -d /tmp/fs-aff3ctsmoke-pip "cmake<4" > /tmp/fs-aff3ctsmoke-pip.log 2>&1; echo "pip download cmake (network) exit $?"; tail -2 /tmp/fs-aff3ctsmoke-pip.log
  ls -la third_party/aff3ct.tar.gz 2>&1
  df -h . /tmp 2>&1 | tail -2
  echo "ALL DONE" ) > logs/run_fs-aff3ctsmoke.out 2>&1
