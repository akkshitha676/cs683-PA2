# Task 1B: Stride Pattern Prefetcher (SPP) — Answers

## Q1. What is the total storage overhead of the prefetcher?

My prefetcher has two tables and a few registers for throttling.

### IP Table (32 entries, fully associative, LRU)

Each entry tracks one load/store instruction (IP).

| Field | Bits | Why this many bits |
|---|---|---|
| valid | 1 | entry is in use or not |
| ip_tag | 10 | IP is hashed down to 10 bits; enough to tell 32 IPs apart |
| last_line | 16 | only the low 16 bits of the last cache line address. Strides are at most ±63 lines, so the low bits are enough to compute the stride |
| last_stride | 7 | signed stride in cache lines, range −63 to +63 (a 4 KB page has 64 lines) |
| uconf | 2 | uniform-stride confidence, counts 0 to 3 |
| sig | 12 | signature: a hash of the last ~4 strides of this IP |
| lru | 5 | LRU position among 32 entries (log2 32 = 5) |
| **Total per entry** | **53** | |

IP Table total = 32 × 53 = **1,696 bits**

### Pattern Table (256 entries, direct mapped, indexed by a hash of the signature)

Each entry says "after this stride history, the next stride is X".

| Field | Bits | Why this many bits |
|---|---|---|
| next_stride | 7 | predicted next stride, −63 to +63 |
| pconf | 2 | confidence of this prediction, 0 to 3 |
| **Total per entry** | **9** | |

Pattern Table total = 256 × 9 = **2,304 bits**

(No tag is needed. If two signatures map to the same entry, the confidence counter
filters out the wrong predictions.)

### Throttling logic

| Register | Bits | Why |
|---|---|---|
| current degree | 2 | degree is 1 to 4, stored as 0 to 3 |
| prefetches sent to L2 in this epoch | 9 | counts up to 256 (the epoch length) |
| useful prefetches in this epoch | 9 | at most 256 in an epoch, saturates |
| **Total** | **20** | |

In my ChampSim code I take snapshots of the cache's existing `pf_lower_level` and
`pf_useful` counters at the start of each epoch, because those counters already
exist in the simulator. In real hardware the same thing is done with the two 9-bit
counters above, which are reset at the start of every epoch.

### Total

| Structure | Bits |
|---|---|
| IP Table | 1,696 |
| Pattern Table | 2,304 |
| Throttling registers | 20 |
| **Total** | **4,020 bits = 502.5 bytes ≈ 0.49 KB** |

The extra counters printed in the final stats (uniform/pattern prefetch counts and
the degree histogram) are only for my analysis, so they are not counted here.

For comparison, the 48 KB L1D itself has 768 lines, so the prefetcher costs only
about 1% of the L1D data storage.

## Q2. What threshold did I use for accuracy throttling, and how did I decide it?

**How the accuracy checker works.** The prefetcher counts how many prefetches it
sent to L2 (prefetches that missed in L1D) and how many of them were later used by a
demand access. After every 256 prefetches (one epoch) it computes

accuracy = useful prefetches / prefetches sent to L2

and picks the degree for the next epoch. This is the same accuracy ChampSim prints
in its stats. I did not use the "ISSUED" count, because 91–96% of issued
prefetches hit in L1D and get dropped. Using it would make the accuracy look like
only a few percent and the prefetcher would always stay at degree 1.

I used an epoch of 256 because it is long enough that one or two lucky or unlucky
prefetches do not change the decision, and short enough to react when the program
changes phase.

**Thresholds I chose: 75%, 50%, 25%.**

| Accuracy | Degree |
|---|---|
| ≥ 75% | 4 |
| 50% – 75% | 3 |
| 25% – 50% | 2 |
| < 25% | 1 |

I started with these because they split the accuracy range into four equal parts,
one for each degree. The 25% point has a simple meaning: below it, 3 out of 4
prefetches are wasted, so the prefetcher should do the minimum.

Then I checked this choice by running two other sets of thresholds on all three
traces (everything else kept the same):

| Thresholds | Trace1 speedup | Trace2 speedup | Trace3 speedup | Geomean speedup | Trace1 acc | Trace2 acc | Trace3 acc |
|---|---|---|---|---|---|---|---|
| 60 / 40 / 20 (lower) | 1.0065 | 1.0017 | 1.0059 | 1.0047 | 52.2% | 38.0% | 31.6% |
| **75 / 50 / 25 (mine)** | **1.0067** | **1.0018** | **1.0055** | **1.0047** | **53.4%** | **40.0%** | **30.4%** |
| 90 / 70 / 50 (higher) | 1.0064 | 1.0019 | 1.0046 | 1.0043 | 55.1% | 41.6% | 27.9% |

What I learned from this:

- **Higher thresholds (90/70/50)** make the prefetcher too careful. On Trace2 it spends
  74% of the time at degree 1. It has the lowest average speedup (1.0043), and Trace3
  loses the most (1.0046 vs 1.0055).
- **Lower thresholds (60/40/20)** give the same average speedup as mine (1.0047). They
  are a little faster on Trace3, but a little slower on Trace1 and Trace2, and less
  accurate on both of those traces. So they send more useless prefetches for no gain
  on average.
- **75/50/25** ties for the best average speedup and keeps accuracy higher than the
  lower thresholds on two of the three traces. So I kept it.

The results are not very sensitive to the exact thresholds. This is expected,
because SPP already filters out bad predictions using its confidence counters
before throttling is even involved.

## Q3. Why these prefetch degrees for the different accuracy ranges?

**The idea.** If my prefetches are mostly correct, I can safely prefetch further
ahead, which makes them more timely and covers more misses. If they are mostly
wrong, every extra prefetch just pollutes the L1D and wastes bandwidth, so I should
prefetch less. That is why degree goes up with accuracy: 1, 2, 3, 4.

**Why a higher degree helps at all.** In my runs, 91–96% of prefetches hit lines
that are already in L1D. This happens because the next 1–2 lines in a pattern were
already prefetched by the previous access. So with degree 1 the prefetcher is often
just "catching up". A larger degree lets it reach lines that are not yet in the
cache, which is where the new coverage comes from.

**Why the minimum is 1 and not 0.** If the degree went to 0, the prefetcher would stop
issuing prefetches, so it could never measure accuracy again and would be stuck off
forever. Degree 1 keeps it learning, and it can climb back up when the program
enters a more regular phase.

**Why the maximum is 4 and not higher.** I compared my design against fixed degrees
and against a more aggressive mapping:

| Degree policy | Trace1 speedup | Trace2 speedup | Trace3 speedup | Geomean speedup | Trace1 acc | Trace2 acc | Trace3 acc |
|---|---|---|---|---|---|---|---|
| Always 1 | 1.0058 | 1.0016 | 1.0049 | 1.0041 | 54.5% | 41.6% | 28.6% |
| Always 4 | 1.0063 | 1.0013 | 1.0066 | 1.0047 | 48.9% | 30.3% | 28.3% |
| 2 / 4 / 6 / 8 (throttled) | 1.0063 | 1.0020 | 1.0066 | 1.0050 | 48.8% | 34.9% | 31.3% |
| **1 / 2 / 3 / 4 (mine, throttled)** | **1.0067** | **1.0018** | **1.0055** | **1.0047** | **53.4%** | **40.0%** | **30.4%** |

- **Always 1** is the slowest on every trace. It does not prefetch far enough ahead.
  It is only slightly more accurate on Trace1 and Trace2, and on Trace3 it is less
  accurate than mine (28.6% vs 30.4%).
- **Always 4** gives the same average speedup as mine (1.0047), but accuracy drops a
  lot (Trace1: 48.9% vs 53.4%, Trace2: 30.3% vs 40.0%). So throttling gets the same
  performance while wasting fewer prefetches.
- **2 / 4 / 6 / 8** is slightly faster on average (1.0050 vs 1.0047, only 0.03%), but
  it is slower on Trace1, and less accurate on Trace1 and Trace2. It issues about
  1.5× as many prefetches and sends 1.3–1.4× as many to L2, for a very small gain.
  In a multi-core system that extra traffic would also hurt the other cores. A small
  gain is not worth that.

**The throttling actually moves.** Over the whole run, the degree is used like this:

| Trace | Degree 1 | Degree 2 | Degree 3 | Degree 4 |
|---|---|---|---|---|
| Trace1 | 4% | 47% | 38% | 11% |
| Trace2 | 39% | 38% | 15% | 9% |
| Trace3 | 31% | 37% | 29% | 4% |

Trace1 has the highest accuracy, so it mostly runs at degrees 2–3 and almost never
drops to 1. Trace2 is the least predictable, so it spends most of its time at
degrees 1–2. Trace3's accuracy is around 30%, so it stays mostly between 1 and 3 and
rarely reaches 4. This is the behaviour I wanted: more aggressive where prefetches
are useful, careful where they are not.
