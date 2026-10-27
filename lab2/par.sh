#!/bin/bash
set -euo pipefail

REPEATS=500
REPEATS_PER_PASS=$((REPEATS / 2))
N=10000000
TARGET=16
PROCS_LIST=$(seq 1 16)

cd "$(dirname "$0")"
gcc -O2 -fopenmp lab2.c -o lab2

export OMP_PLACES=threads
export OMP_PROC_BIND=TRUE

echo "threads,repeat,time_s" > measurements.csv
echo "Сбор $REPEATS измерений для каждого числа потоков двумя проходами..."
for p in $PROCS_LIST; do
    echo "Первый проход: $p потоков..."
    ./lab2 "$p" "$N" "$TARGET" "$REPEATS_PER_PASS" measurements.csv 0
done
for ((p = 16; p >= 1; p--)); do
    echo "Обратный проход: $p потоков..."
    ./lab2 "$p" "$N" "$TARGET" "$REPEATS_PER_PASS" measurements.csv "$REPEATS_PER_PASS"
done

python3 analyze_bench.py
python3 plot.py
rm -f measurements.csv time_vs_p.csv speedup.csv
echo "Сырые измерения удалены; оставлена сводная таблица results.csv."
