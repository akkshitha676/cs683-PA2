#!/bin/bash
# Task 1 runs: 25M warmup + 25M simulation instructions per trace.
# Usage: scripts/run_task1.sh <label> <binary-name-in-bin/>
# Output: results/task1/<label>_<Trace>.txt (one file per trace, run in parallel)
set -u
cd "$(dirname "$0")/.."
LABEL=$1
BIN=bin/$2
WARMUP=25000000
SIM=25000000
OUT=results/task1
mkdir -p "$OUT"
for t in traces/Trace*.gz; do
    name=$(basename "$t" .gz)
    "$BIN" -warmup_instructions $WARMUP -simulation_instructions $SIM -traces "$t" \
        > "$OUT/${LABEL}_${name}.txt" 2>&1 &
done
wait
