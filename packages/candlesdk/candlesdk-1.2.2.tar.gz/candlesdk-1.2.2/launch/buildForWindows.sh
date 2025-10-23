#!/bin/bash

set -e
BUILD_DIRECTORY=build
start_dir=$(pwd)
base_dir="$(dirname "$(dirname "$(readlink -f "${BASH_SOURCE}")")")" # CANdle SDK directory
cd ${base_dir}

mkdir $BUILD_DIRECTORY -p
cd $BUILD_DIRECTORY
chmod -R a+rw ${base_dir}/${BUILD_DIRECTORY}
cmake .. -DCMAKE_TOOLCHAIN_FILE=${base_dir}/cmake/windows.x86_64.gcc.toolchain.cmake
chmod -R a+rw ${base_dir}/${BUILD_DIRECTORY}
make -j
chmod -R a+rw ${base_dir}/${BUILD_DIRECTORY}
cpack -G NSIS
chmod -R a+rw ${base_dir}/${BUILD_DIRECTORY}

cd ${start_dir}
