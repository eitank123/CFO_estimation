#!/bin/bash
# fs-aff3ct: build AFF3CT v4.7.3 (Release: CLI aff3ct-bin + fullsys/aff3ct_tools/aff3ct_vec) and dump bit-exact DVB-RCS2 turbo encoder vectors to fullsys/results/aff3ct_vectors (checked by fullsys/compare_aff3ct.py)
cd /gpfs0/bgu-haimp/users/karpei/CFO_estimation
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
PY=/gpfs0/bgu-haimp/users/karpei/env/polar-sionna/bin/python
mkdir -p logs fullsys/results
( OUT=fullsys/results/aff3ct_vectors; SRC=third_party/aff3ct; BLD=third_party/aff3ct_build; TOOLS=$PWD/third_party/pytools
  mkdir -p $OUT
  echo "host $(hostname)  nproc $(nproc)  start $(date)"
  # ---- sources: the pushed tarball (no .git: versions passed by AFF3CT_OVERRIDE_VERSION / SPU_OVERRIDE_VERSION)
  if [ ! -f $SRC/CMakeLists.txt ]; then
    tar xzf third_party/aff3ct.tar.gz -C third_party || { echo "FAILED: untar third_party/aff3ct.tar.gz"; exit 1; }
  fi
  # ---- toolchain: C++ compiler required; cmake / ninja from pip into a job-local folder if missing (env untouched)
  CXXB=$(command -v g++ || command -v c++ || command -v clang++)
  [ -z "$CXXB" ] && { echo "FAILED: no C++ compiler (g++ / c++ / clang++) on the compute node, cannot build AFF3CT"; exit 1; }
  CCB=$(command -v gcc || command -v cc || echo $CXXB)                      # lib/cli enables C as well
  echo "C++: $CXXB | $($CXXB --version | head -1)  C: $CCB"
  CMAKE=$(command -v cmake)
  if [ -z "$CMAKE" ]; then
    [ -x $TOOLS/cmake/data/bin/cmake ] || $PY -m pip install --target $TOOLS "cmake<4" || { echo "FAILED: pip install cmake"; exit 1; }
    CMAKE=$TOOLS/cmake/data/bin/cmake
  fi
  GEN=""
  if ! command -v make > /dev/null; then
    [ -x $TOOLS/ninja/data/bin/ninja ] || $PY -m pip install --target $TOOLS ninja || { echo "FAILED: no make and pip install ninja failed"; exit 1; }
    GEN="-G Ninja -DCMAKE_MAKE_PROGRAM=$TOOLS/ninja/data/bin/ninja"
  fi
  echo "cmake: $CMAKE | $($CMAKE --version | head -1)  generator: ${GEN:-Unix Makefiles}"
  # ---- configure + build (CLI first; aff3ct_vec reuses the same objects through the static library)
  $CMAKE -S fullsys/aff3ct_tools -B $BLD $GEN -DAFF3CT_DIR=$PWD/$SRC -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=$CXXB -DCMAKE_C_COMPILER=$CCB \
    -DAFF3CT_OVERRIDE_VERSION=v4.7.3 -DSPU_OVERRIDE_VERSION=v1.10.0 -DSPU_STACKTRACE=OFF -DSPU_STACKTRACE_SEGFAULT=OFF \
    -DSPU_TESTS=OFF -DSPU_BENCHMARK=OFF -DCMAKE_POLICY_VERSION_MINIMUM=3.5 || { echo "FAILED: cmake configure"; exit 1; }
  $CMAKE --build $BLD --target aff3ct-bin -- -j16 || { echo "FAILED: build aff3ct-bin"; exit 1; }
  BIN=$(find $BLD -type f -name 'aff3ct-[0-9]*' -perm -u+x | grep '/bin/' | head -1)
  [ -z "$BIN" ] && { echo "FAILED: aff3ct binary not found under $BLD"; exit 1; }
  echo "binary: $BIN  built $(date)"
  $BIN --version 2>&1 | head -5
  VEC_OK=1
  $CMAKE --build $BLD --target aff3ct_vec -- -j16 || { echo "WARNING: aff3ct_vec build failed (CLI dumps still produced)"; VEC_OK=0; }
  # ---- CLI debug dumps: 3 frames at Eb/N0 10 dB, 1 thread, fixed seed, whole frames (-d), CRC 32-GZIP as the refs
  $BIN -C TURBO_DB -K 1504 -N 3008 --enc-sub-std DVB-RCS2 -h > $OUT/cli_help_turbo_db.txt 2>&1
  for KN in 1504:3008 984:2952 304:912 1504:4512; do
    K=${KN%:*}; N=${KN#*:}
    $BIN --sim-type BFER -C TURBO_DB -K $K -N $N --enc-sub-std DVB-RCS2 -i 8 --mdm-type PSK --mdm-bps 2 \
      --crc-poly 32-GZIP --dec-sf-type ADAPTIVE -m 10 -M 10 --sim-max-fra 3 --mnt-max-fe 1 --sim-threads 1 \
      --sim-seed 1234 --sim-dbg --sim-dbg-limit 100000 > $OUT/cli_K${K}_N${N}.txt 2>&1
    echo "cli K=$K N=$N exit $?  encode calls $(grep -c 'Encoder_turbo_DB::encode' $OUT/cli_K${K}_N${N}.txt)"
    grep -m3 -iE 'error|unsupported|no DVB-RCS2 parameters' $OUT/cli_K${K}_N${N}.txt
  done
  # ---- direct module dumps (LUT, lut_inv, CRC, encoder 3K output, puncturer) for the same cases + the interleaver table probe
  if [ $VEC_OK = 1 ]; then
    VEC=$(find $BLD -type f -name aff3ct_vec -perm -u+x | head -1)
    $VEC $OUT 1234 1504:3008 984:2952 304:912 1504:4512; echo "aff3ct_vec exit $?"
  fi
  ls -la $OUT
  md5sum $OUT/* 2>/dev/null
  echo "end $(date)"
  echo "ALL DONE" ) > logs/run_fs-aff3ct.out 2>&1
