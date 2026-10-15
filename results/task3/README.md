# Task 3 comparison dataset

This directory contains five Task 3 configurations on Trace1-002, Trace2-003, and Trace3-001: baseline (no prefetcher + LRU), SPP-only (SPP + LRU), Dynamic I-RRIP-only (20%), combined SPP + Dynamic I-RRIP (20%, awareness enabled), and combined SPP + Dynamic I-RRIP (20%, unused-prefetch victim awareness disabled). Every source log requests 25,000,000 warmup and 25,000,000 simulation instructions.

## Source logs and validation

- Baseline and SPP-only logs and command/exit records: results/raw_logs/pa2-baseline-spp-20261015.QZXnVo/.
- Dynamic I-RRIP-only 20% logs and sidecars are consolidated at results/raw_logs/task2b-dyn-irrip-sensitivity/ (selected from /tmp/pa2-task2b-sensitivity.4P63eI/). The commands use dyn_irrip_t20; the saved policy snapshot implements 5 * instruction_score >= total_score. The subdirectory also retains the full sensitivity-study logs and metadata.
- Combined 20% logs and sidecars are consolidated at results/raw_logs/task3-combined-20pct/ (from /tmp/pa2-task3-final-20pct.L1YbrH/).
- Awareness-disabled combined ablation logs and command/exit records are in results/raw_logs/task3-ablation-no-prefetch-awareness/. It disables only the unused-prefetched-victim selection branch; Trace2-003 uses the successful retry log Trace2-003-no-awareness-retry.log. The original interrupted Trace2 log was lost during recovery and is not used as a completed run.
- All 15 run exit records contain 0. Every log reports the requested warmup/simulation settings, all CPUs completed, and ROI statistics. The ablation Trace2-003 and Trace3-001 runs report 25,000,001 finished ROI instructions after the 25,000,000-instruction request; the count is retained in the CSV. Across the dataset, Trace1-002 reports 25,000,000 and Trace2-003/Trace3-001 report 25,000,001. For all runs, L1D LOAD misses divided by 25,000,000 simulation instructions reproduces the logged L1D load MPKI within display precision.
- IPC and cache MPKI values are taken from logs. Speedup uses logged configuration IPC divided by the same trace's baseline logged IPC.

## Definitions

- Speedup = configuration IPC / matching baseline IPC.
- ChampSim prefetch accuracy = useful / lower_level from the L1D prefetch statistics. It is NA for configurations with no active prefetcher.
- SPP resolved-prefetch accuracy = useful / (useful + useless), from the SPP output. This uses a different denominator from ChampSim accuracy.
- Coverage (%) = 100 × (baseline L1D load misses − configuration L1D load misses) / baseline L1D load misses. It uses the L1D LOAD miss count, not total L1D MPKI; baseline coverage is 0%.
- Unsupported or inapplicable fields are NA. No prefetch accuracy is imputed for runs without a prefetcher.

## Files

- data/task3_comparison.csv: 15 configuration/trace rows, source paths, status/completion fields, counters (including unused-prefetch victim selections where applicable) and derived metrics.
- data/task3_comparison.pre-ablation.csv: preserved 12-row dataset from before the ablation was added.
- plots/ipc_by_configuration.svg
- plots/speedup_vs_baseline.svg (zoomed scale begins at 0.98 and is explicitly labeled; baseline reference 1.0)
- plots/l1d_load_mpki.svg
- plots/prefetch_accuracy.svg (bars are ChampSim accuracy; open circles are SPP resolved accuracy; formulas are labeled)
- plots/l1d_load_miss_coverage.svg
- plots/l2c_load_mpki.svg
- plots/l2c_instruction_and_data_load_mpki.svg

Figures are vector SVGs with units, trace names, configuration labels and legends. Bar charts use zero baselines; speedup and coverage include their reference lines. No Task 1, Task 2A or Task 2B plots are included.


Updated 300-DPI PNG figures for the five-configuration comparison are in plots_png/ (the original SVGs in plots/ are unchanged): ipc_by_configuration.png, speedup_vs_baseline.png, l1d_load_mpki.png, prefetch_accuracy.png, l1d_load_miss_coverage.png, l2c_load_mpki.png, and l2c_instruction_and_data_load_mpki.png. The speedup figure explicitly labels its zoomed 0.95 axis start.
