#!/usr/bin/env python3
"""Task 1 deliverables: results table (CSV + Markdown) and the four plots.
Usage: .venv/bin/python scripts/task1_plots.py
Reads  results/task1/{baseline,ip_stride,spp}_<Trace>.txt
Writes results/task1/task1_table.{csv,md} and results/task1/plots/*.png"""
import os, csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from task1_compare import load, ROOT

CONFIGS = [('baseline', 'Baseline'), ('ip_stride', 'IP-stride'), ('spp', 'SPP')]
# Color follows the entity: baseline is a neutral reference, prefetchers are categorical slots 1-2.
COLORS = {'baseline': '#8a8a85', 'ip_stride': '#2a78d6', 'spp': '#eb6834'}
INK, MUTED, GRID = '#1f1f1e', '#6b6b66', '#e4e4e0'

runs = load([ROOT])
base = runs['baseline']
traces = sorted(base)

rows = []
for key, name in CONFIGS:
    for t in traces:
        r = runs[key][t]
        prefetching = key != 'baseline'
        rows.append(dict(
            trace=t, config=name, ipc=r['ipc'],
            speedup=r['ipc'] / base[t]['ipc'],
            l1d_load_mpki=r['mpki'],
            accuracy=r['acc'] if prefetching else None,
            coverage=100 * (base[t]['miss'] - r['miss']) / base[t]['miss'] if prefetching else None))

def fmt(v, nd):
    return '-' if v is None else f'{v:.{nd}f}'

with open(os.path.join(ROOT, 'task1_table.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

with open(os.path.join(ROOT, 'task1_table.md'), 'w') as f:
    f.write('| Trace | Config | IPC | Speedup | L1D Load MPKI | Accuracy (%) | Coverage (%) |\n')
    f.write('|---|---|---|---|---|---|---|\n')
    for r in sorted(rows, key=lambda r: r['trace']):
        f.write(f"| {r['trace']} | {r['config']} | {r['ipc']:.4f} | {r['speedup']:.4f} | "
                f"{r['l1d_load_mpki']:.3f} | {fmt(r['accuracy'], 2)} | {fmt(r['coverage'], 2)} |\n")

def value(key, t, metric):
    return next(r[metric] for r in rows if r['config'] == dict(CONFIGS)[key] and r['trace'] == t)

def style(ax, ylabel, title):
    ax.set_title(title, color=INK, fontsize=12, loc='left', pad=12)
    ax.set_ylabel(ylabel, color=MUTED)
    ax.set_xticks(np.arange(len(traces)))
    ax.set_xticklabels(traces, color=INK)
    ax.tick_params(colors=MUTED, length=0)
    ax.grid(axis='y', color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ('top', 'right', 'left'):
        ax.spines[s].set_visible(False)
    ax.spines['bottom'].set_color(MUTED)

def bars(keys, metric, ylabel, title, fname, base_at=0.0, nd=2, ref_line=None):
    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=150)
    x = np.arange(len(traces))
    width = 0.8 / len(keys)
    tops = []
    for i, key in enumerate(keys):
        vals = np.array([value(key, t, metric) for t in traces])
        pos = x + (i - (len(keys) - 1) / 2) * width
        # Bars grow from base_at (1.0 for speedup) so bar length is the gain itself.
        b = ax.bar(pos, vals - base_at, width * 0.92, bottom=base_at,
                   color=COLORS[key], label=dict(CONFIGS)[key], zorder=3)
        ax.bar_label(b, labels=[f'{v:.{nd}f}' for v in vals], padding=2, fontsize=8, color=INK)
        tops.extend(vals)
    if ref_line is not None:
        ax.axhline(ref_line, color=MUTED, linestyle='--', linewidth=1, zorder=4,
                   label='Baseline (no prefetching)')
    lo, hi = min(tops + [base_at]), max(tops + [base_at])
    pad = (hi - lo) * 0.15 or 0.01
    ax.set_ylim(min(base_at, lo) - (pad if base_at else 0), hi + pad)
    style(ax, ylabel, title)
    ax.legend(frameon=False, fontsize=9, labelcolor=INK, loc='upper left', ncol=len(keys) + 1)
    fig.tight_layout()
    fig.savefig(os.path.join(ROOT, 'plots', fname))
    plt.close(fig)

os.makedirs(os.path.join(ROOT, 'plots'), exist_ok=True)
bars(['ip_stride', 'spp'], 'speedup', 'Speedup', 'Speedup of L1D prefetchers over baseline (no prefetching)',
     'speedup.png', base_at=1.0, nd=4, ref_line=1.0)
bars(['baseline', 'ip_stride', 'spp'], 'l1d_load_mpki', 'L1D Load MPKI', 'L1D load MPKI (lower is better)',
     'mpki.png')
bars(['ip_stride', 'spp'], 'accuracy', 'L1D prefetch accuracy (%)', 'L1D prefetch accuracy',
     'accuracy.png', nd=1)
bars(['ip_stride', 'spp'], 'coverage', 'L1D prefetch coverage (%)', 'L1D prefetch coverage',
     'coverage.png', nd=1)

print(open(os.path.join(ROOT, 'task1_table.md')).read())
