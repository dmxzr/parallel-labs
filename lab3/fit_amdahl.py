#!/usr/bin/env python3
import argparse
import csv
import math
from pathlib import Path
from typing import Iterable, Tuple


def theoretical_speedup(threads: int, parallel_fraction: float) -> float:
    return 1.0 / ((1.0 - parallel_fraction) + parallel_fraction / threads)


def overhead_speedup(threads: int, parallel_fraction: float, overhead: float) -> float:
    denominator = (
        (1.0 - parallel_fraction)
        + parallel_fraction / threads
        + overhead * (threads - 1)
    )
    return 1.0 / denominator


def fit_amdahl_model(
    measurements: Iterable[Tuple[int, float]],
) -> Tuple[float, float, int]:
    points = [
        (threads, speedup)
        for threads, speedup in measurements
        if threads > 1 and math.isfinite(speedup) and speedup > 0
    ]
    if not points:
        raise ValueError("Нет корректных измерений для потоков p > 1.")

    required_alpha = [
        (1.0 - 1.0 / speedup) / (1.0 - 1.0 / threads)
        for threads, speedup in points
    ]
    alpha = max(required_alpha, default=0.0)
    if alpha > 1.0 + 1e-6:
        raise ValueError(
            "Измеренное ускорение превышает число потоков; проверьте сопоставимость "
            "последовательной и параллельной версий и повторите замер."
        )
    alpha = min(1.0, max(0.0, alpha))

    def squared_error(overhead: float) -> float:
        return sum(
            (overhead_speedup(threads, alpha, overhead) - speedup) ** 2
            for threads, speedup in points
        )

    left, right = 0.0, 2.0
    ratio = (math.sqrt(5.0) - 1.0) / 2.0
    x1 = right - ratio * (right - left)
    x2 = left + ratio * (right - left)
    f1, f2 = squared_error(x1), squared_error(x2)
    for _ in range(100):
        if f1 <= f2:
            right, x2, f2 = x2, x1, f1
            x1 = right - ratio * (right - left)
            f1 = squared_error(x1)
        else:
            left, x1, f1 = x1, x2, f2
            x2 = left + ratio * (right - left)
            f2 = squared_error(x2)
    overhead = (left + right) / 2.0
    return alpha, overhead, len(points)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Подбор доли параллельной части, ограничивающей измеренные ускорения сверху."
    )
    parser.add_argument(
        "csv_file",
        nargs="?",
        type=Path,
        default=Path(__file__).parent / "results" / "results.csv",
        help="сводная таблица benchmark.py",
    )
    args = parser.parse_args()

    try:
        with args.csv_file.open(encoding="utf-8-sig", newline="") as file:
            rows = list(csv.DictReader(file))
        measurements = [
            (int(row["Потоки"]), float(row["Экспериментальное ускорение"]))
            for row in rows
        ]
        alpha, overhead, included = fit_amdahl_model(measurements)
    except (OSError, KeyError, ValueError) as error:
        parser.error(str(error))

    print(f"Подобранная доля параллельной части α = {alpha:.6f} ({alpha:.2%})")
    print(f"Подобранный коэффициент накладных расходов β = {overhead:.6f}")
    print(f"Данные p=2..16 лежат не выше чистой кривой Амдала: {included}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
