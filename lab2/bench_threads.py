#!/usr/bin/env python3
import csv
import math
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BIN = os.path.join(ROOT, 'lab2')
RESULT_CSV = os.path.join(ROOT, 'thread_bench.csv')
SUMMARY_CSV = os.path.join(ROOT, 'thread_bench_summary.csv')
COUNT = 10000000
TARGET = 16
REPEATS = 100


def get_thread_list():
    max_threads = os.cpu_count() or 1
    values = []
    p = 1
    while p <= max_threads:
        values.append(p)
        p *= 2
    if values and values[-1] != max_threads:
        values.append(max_threads)
    return values


def build_binary():
    subprocess.run(['gcc', '-O2', '-fopenmp', 'lab2.c', '-o', 'lab2'], cwd=ROOT, check=True)


def run_once(threads):
    result = subprocess.run(
        [BIN, str(threads), str(COUNT), str(TARGET)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    match = re.search(r'time=([0-9.]+)', result.stdout)
    if not match:
        raise RuntimeError(f'Could not parse benchmark output for threads={threads}: {result.stdout!r}')
    return float(match.group(1))


def main():
    build_binary()
    threads_list = get_thread_list()
    rows = []
    for threads in threads_list:
        times = []
        for _ in range(REPEATS):
            times.append(run_once(threads))
        avg = sum(times) / len(times)
        std = math.sqrt(sum((t - avg) ** 2 for t in times) / len(times))
        best = min(times)
        worst = max(times)
        rows.append({
            'threads': threads,
            'count': COUNT,
            'target': TARGET,
            'repeats': REPEATS,
            'avg_time_s': avg,
            'min_time_s': best,
            'max_time_s': worst,
            'stddev_s': std,
        })
        print(f"threads={threads}: avg={avg:.6f}s min={best:.6f}s max={worst:.6f}s std={std:.6f}s")

    with open(RESULT_CSV, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['threads', 'count', 'target', 'repeats', 'avg_time_s', 'min_time_s', 'max_time_s', 'stddev_s'])
        writer.writeheader()
        writer.writerows(rows)

    seq = next(r for r in rows if r['threads'] == 1)
    summary = []
    for row in rows:
        speedup = seq['avg_time_s'] / row['avg_time_s']
        efficiency = speedup / row['threads']
        summary.append({
            'threads': row['threads'],
            'avg_time_s': row['avg_time_s'],
            'speedup': speedup,
            'efficiency': efficiency,
            'theoretical_speedup': row['threads'],
        })

    with open(SUMMARY_CSV, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['threads', 'avg_time_s', 'speedup', 'efficiency', 'theoretical_speedup'])
        writer.writeheader()
        writer.writerows(summary)

    print(f'Wrote {RESULT_CSV}')
    print(f'Wrote {SUMMARY_CSV}')


if __name__ == '__main__':
    main()
