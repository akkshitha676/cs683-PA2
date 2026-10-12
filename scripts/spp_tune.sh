#!/bin/bash
# Build SPP variants with #define overrides, then run all of them on all traces.
# Usage: scripts/spp_tune.sh "name1:DEF=VAL,DEF=VAL" "name2:DEF=VAL" ...
# Output: results/task1/tuning/<name>_<Trace>.txt
set -eu
cd "$(dirname "$0")/.."
export CXX=${CXX:-$(command -v g++-7 || echo g++)}   # GCC 7: newer GCC builds crash
OUT=results/task1/tuning
mkdir -p "$OUT"
JOBS=()
for spec in "$@"; do
    name=${spec%%:*}
    defs=${spec#*:}
    src=prefetcher/spp_${name}.l1d_pref
    cp prefetcher/spp.l1d_pref "$src"
    IFS=',' read -ra kv <<< "$defs"
    for d in "${kv[@]}"; do
        [ -z "$d" ] && continue
        sed -i -E "s/^(#define ${d%%=*}[[:space:]]+)[^[:space:]]+/\1${d#*=}/" "$src"
        grep -qE "^#define ${d%%=*}[[:space:]]+${d#*=}([[:space:]]|$)" "$src" || { echo "bad define $d"; exit 1; }
    done
    ./build_champsim.sh spp_${name} lru ${name} > /dev/null 2>&1
    rm -f "$src"
    bin=hashed_perceptron-no-spp_${name}-no-no-no-no-no-lru-lru-lru-lru-lru-lru-lru-lru-1core-${name}
    [ -x bin/$bin ] || { echo "build failed: $name"; exit 1; }
    for t in traces/Trace*.gz; do
        JOBS+=("$bin $t $OUT/${name}_$(basename $t .gz).txt")
    done
done
printf '%s\n' "${JOBS[@]}" | xargs -P "$(nproc)" -L 1 sh -c \
    'bin/$0 -warmup_instructions 25000000 -simulation_instructions 25000000 -traces $1 > $2 2>&1'
