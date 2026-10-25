#!/usr/bin/env python3
import csv
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.abspath(__file__))
SUMMARY = os.path.join(ROOT, 'thread_bench_summary.csv')
OUT_DIR = ROOT


def load_rows(path):
    with open(path, newline='') as f:
        return list(csv.DictReader(f))


def main():
    rows = load_rows(SUMMARY)
    threads = [int(r['threads']) for r in rows]
    times = [float(r['avg_time_s']) for r in rows]
    speedups = [float(r['speedup']) for r in rows]
    efficiencies = [float(r['efficiency']) for r in rows]
    theoretical = [float(r['theoretical_speedup']) for r in rows]

    fig1, ax1 = plt.subplots(figsize=(8, 5))
    ax1.plot(threads, times, marker='o', linewidth=2, color='tab:blue', label='Experimental time')
    ax1.set_title('Time vs number of threads')
    ax1.set_xlabel('Threads')
    ax1.set_ylabel('Average time, s')
    ax1.grid(True, linestyle='--', alpha=0.4)
    fig1.tight_layout()
    fig1.savefig(os.path.join(OUT_DIR, 'time_vs_threads.png'))
    plt.close(fig1)

    fig2, ax2 = plt.subplots(figsize=(8, 5))
    ax2.plot(threads, speedups, marker='o', linewidth=2, color='tab:green', label='Experimental speedup')
    ax2.plot(threads, theoretical, linestyle='--', marker='s', linewidth=2, color='tab:red', label='Ideal speedup')
    ax2.set_title('Speedup vs number of threads')
    ax2.set_xlabel('Threads')
    ax2.set_ylabel('Speedup')
    ax2.grid(True, linestyle='--', alpha=0.4)
    ax2.legend()
    fig2.tight_layout()
    fig2.savefig(os.path.join(OUT_DIR, 'speedup_vs_threads.png'))
    plt.close(fig2)

    fig3, ax3 = plt.subplots(figsize=(8, 5))
    ax3.plot(threads, efficiencies, marker='o', linewidth=2, color='tab:purple', label='Efficiency')
    ax3.axhline(1.0, color='black', linestyle='--', linewidth=1, label='Ideal efficiency')
    ax3.set_title('Efficiency vs number of threads')
    ax3.set_xlabel('Threads')
    ax3.set_ylabel('Efficiency')
    ax3.grid(True, linestyle='--', alpha=0.4)
    ax3.legend()
    fig3.tight_layout()
    fig3.savefig(os.path.join(OUT_DIR, 'efficiency_vs_threads.png'))
    plt.close(fig3)

    print('Created time_vs_threads.png')
    print('Created speedup_vs_threads.png')
    print('Created efficiency_vs_threads.png')


if __name__ == '__main__':
    main()
