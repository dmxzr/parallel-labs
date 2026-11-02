#!/bin/bash
set -euo pipefail

REPEATS=500
REPEATS_PER_PASS=$((REPEATS / 2))
N=10000000
TARGET=16
RESULT_TAG=${RESULT_TAG:-$(uname -s | tr '[:upper:]' '[:lower:]')_$(uname -m)}

cd "$(dirname "$0")"
MEASUREMENTS="measurements_${RESULT_TAG}.csv"
RESULTS="results_${RESULT_TAG}.csv"
BINARY="lab2_${RESULT_TAG}"
OUTPUTS=(
    "$MEASUREMENTS"
    "$RESULTS"
    "$BINARY"
    "graph1_time_vs_p_${RESULT_TAG}.png"
    "graph2_speedup_${RESULT_TAG}.png"
    "graph3_efficiency_${RESULT_TAG}.png"
    "graph4_time_system_comparison_${RESULT_TAG}.png"
    "graph5_speedup_system_comparison_${RESULT_TAG}.png"
)

for output in "${OUTPUTS[@]}"; do
    if [[ -e "$output" ]]; then
        echo "Refusing to overwrite existing file: $output" >&2
        exit 1
    fi
done

"${CC:-gcc}" -O2 -fopenmp lab2.c -o "$BINARY"

export OMP_PROC_BIND=FALSE
unset OMP_PLACES

echo "threads,repeat,time_s" > "$MEASUREMENTS"
echo "Сбор $REPEATS измерений для каждого числа потоков двумя проходами..."
for p in $(seq 1 16); do
    echo "Первый проход: $p потоков..."
    "./$BINARY" "$p" "$N" "$TARGET" "$REPEATS_PER_PASS" "$MEASUREMENTS" 0
done
for ((p = 16; p >= 1; p--)); do
    echo "Обратный проход: $p потоков..."
    "./$BINARY" "$p" "$N" "$TARGET" "$REPEATS_PER_PASS" "$MEASUREMENTS" "$REPEATS_PER_PASS"
done

python3 analyze_bench.py --input "$MEASUREMENTS" --output "$RESULTS"
if [[ -f results_linux.csv ]]; then
    python3 plot.py --input "$RESULTS" --compare results_linux.csv --suffix "_${RESULT_TAG}"
else
    python3 plot.py --input "$RESULTS" --suffix "_${RESULT_TAG}"
fi
echo "Сырые измерения сохранены в $MEASUREMENTS."
echo "Сводная таблица и графики сохранены с суффиксом _${RESULT_TAG}."
