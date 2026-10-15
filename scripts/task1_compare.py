#!/usr/bin/env python3
"""Compare Task 1 runs against baseline.
Usage: scripts/task1_compare.py [dir ...]   (default: results/task1 results/task1/tuning)
Reads <label>_<Trace>.txt files; baseline is results/task1/baseline_<Trace>.txt."""
import re, sys, glob, os
from collections import defaultdict

ROOT = os.path.join(os.path.dirname(__file__), '..', 'results', 'task1')

def parse(path):
    txt = open(path).read()
    if 'Allocated PAGES' not in txt:
        return None
    ipc = float(re.search(r'CPU 0 cumulative IPC: ([\d.]+)', txt).group(1))
    m = re.search(r'^L1D LOAD\s+ACCESS:\s+\d+\s+HIT:\s+\d+\s+MISS:\s+(\d+).*MPKI: ([\d.]+)', txt, re.M)
    acc = re.search(r'L1D USEFUL LOAD PREFETCHES:.*ACCURACY: ([\d.]+|-?nan)', txt).group(1)
    return dict(ipc=ipc, miss=int(m.group(1)), mpki=float(m.group(2)),
                acc=float(acc) if 'nan' not in acc else None)

def load(dirs):
    runs = defaultdict(dict)
    for d in dirs:
        for f in sorted(glob.glob(os.path.join(d, '*_Trace*.txt'))):
            label, trace = os.path.basename(f)[:-4].rsplit('_', 1)
            r = parse(f)
            if r:
                runs[label][trace] = r
    return runs

def main():
    dirs = sys.argv[1:] or [ROOT, os.path.join(ROOT, 'tuning')]
    runs = load(dirs)
    base = load([ROOT])['baseline']
    traces = sorted(base)

    print(f"{'config':<14}" + ''.join(f"{t+' spd':>12}{'cov%':>7}{'acc%':>7}" for t in traces) + f"{'geo spd':>9}")
    for label, r in runs.items():
        if label == 'baseline' or any(t not in r for t in traces):
            continue
        row, g = f"{label:<14}", 1.0
        for t in traces:
            spd = r[t]['ipc'] / base[t]['ipc']
            cov = 100 * (base[t]['miss'] - r[t]['miss']) / base[t]['miss']
            acc = r[t]['acc'] or 0
            row += f"{spd:>12.4f}{cov:>7.2f}{acc:>7.1f}"
            g *= spd
        print(row + f"{g ** (1 / len(traces)):>9.4f}")

if __name__ == '__main__':
    main()
