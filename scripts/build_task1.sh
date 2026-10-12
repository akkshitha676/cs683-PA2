#!/bin/bash
# Build the three Task 1 binaries: baseline (no prefetcher), IP-stride, SPP.
# Uses g++-7 if installed (README requirement; newer GCC builds crash), else g++.
# Override with: CXX=/path/to/g++ scripts/build_task1.sh
set -eu
cd "$(dirname "$0")/.."
export CXX=${CXX:-$(command -v g++-7 || echo g++)}
echo "Using CXX=$CXX ($($CXX -dumpversion))"
./build_champsim.sh no lru baseline
./build_champsim.sh ip_stride lru ip_stride
./build_champsim.sh spp lru spp
