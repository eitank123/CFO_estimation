# Wrapper build for the AFF3CT test vectors (jobs/fs-aff3ct.sh): the AFF3CT CLI (aff3ct-bin) and aff3ct_vec,
# a small program that drives the AFF3CT DVB-RCS2 modules directly (CRC 32-GZIP, Encoder_turbo_DB,
# Puncturer_turbo_DB, Interleaver_core_ARP_DVB_RCS2) and writes the LUTs and encoder vectors as text.
# Configure: cmake -S fullsys/aff3ct_tools -B <build> -DAFF3CT_DIR=<aff3ct source> -DCMAKE_BUILD_TYPE=Release
cmake_minimum_required(VERSION 3.5)
project(aff3ct_vectors CXX)

set(AFF3CT_DIR "" CACHE PATH "AFF3CT source folder (third_party/aff3ct)")
if(NOT EXISTS "${AFF3CT_DIR}/CMakeLists.txt")
    message(FATAL_ERROR "AFF3CT_DIR='${AFF3CT_DIR}' has no CMakeLists.txt")
endif()

set(AFF3CT_COMPILE_EXE        ON  CACHE BOOL "" FORCE)
set(AFF3CT_COMPILE_STATIC_LIB ON  CACHE BOOL "" FORCE)   # archive of the same objects, links aff3ct_vec
set(AFF3CT_COMPILE_SHARED_LIB OFF CACHE BOOL "" FORCE)
add_subdirectory("${AFF3CT_DIR}" aff3ct)

add_executable(aff3ct_vec aff3ct_vec.cpp)
target_link_libraries(aff3ct_vec PRIVATE aff3ct-static-lib)
