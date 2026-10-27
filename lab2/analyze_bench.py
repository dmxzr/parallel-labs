#!/usr/bin/env python3
import csv
import math
import os
import statistics

ROOT = os.path.dirname(os.path.abspath(__file__))
REPEATS = 500
FIT_MAX_THREADS = 4


def read_samples():
    samples = {}
    with open(os.path.join(ROOT, "measurements.csv"), newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            threads = int(row["threads"])
            samples.setdefault(threads, []).append(float(row["time_s"]))
    return samples


def amdahl_speedup(threads, alpha):
    return 1.0 / ((1.0 - alpha) + alpha / threads)


def fit_alpha(mean_times):
    baseline = mean_times[1]
    measured_speedups = {
        threads: baseline / mean_times[threads] for threads in mean_times
    }
    fit_threads = [
        threads for threads in sorted(mean_times) if threads <= FIT_MAX_THREADS
    ]

    best_alpha = None
    best_rmse = float("inf")
    for hundredths in range(10, 99):
        alpha = hundredths / 100.0
        rmse = math.sqrt(
            sum(
                (measured_speedups[p] - amdahl_speedup(p, alpha)) ** 2
                for p in fit_threads
            )
            / len(fit_threads)
        )
        if rmse < best_rmse:
            best_alpha = alpha
            best_rmse = rmse

    return best_alpha, best_rmse, measured_speedups


def main():
    samples = read_samples()
    expected_threads = set(range(1, 17))
    if set(samples) != expected_threads:
        raise ValueError(
            f"Expected measurements for thread counts 1..16; got {sorted(samples)}"
        )
    for threads, values in samples.items():
        if len(values) != REPEATS:
            raise ValueError(
                f"Expected {REPEATS} measurements for {threads} threads; got {len(values)}"
            )

    mean_times = {
        threads: statistics.mean(values) for threads, values in samples.items()
    }
    alpha, rmse, experimental_speedups = fit_alpha(mean_times)

    result_path = os.path.join(ROOT, "results.csv")
    fields = [
        "потоки",
        "экспериментальное_время_среднее_с",
        "экспериментальное_ускорение",
        "экспериментальная_эффективность",
        "теоретическое_ускорение",
        "теоретическая_эффективность",
        "отклонение_ускорения_проц",
        "альфа_подбора",
    ]
    with open(result_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for threads in sorted(samples):
            theoretical_speedup = amdahl_speedup(threads, alpha)
            experimental_speedup = experimental_speedups[threads]
            deviation = (
                100.0
                * abs(experimental_speedup - theoretical_speedup)
                / theoretical_speedup
            )
            writer.writerow(
                {
                    "потоки": threads,
                    "экспериментальное_время_среднее_с": f"{mean_times[threads]:.8f}",
                    "экспериментальное_ускорение": f"{experimental_speedup:.6f}",
                    "экспериментальная_эффективность": f"{experimental_speedup / threads:.6f}",
                    "теоретическое_ускорение": f"{theoretical_speedup:.6f}",
                    "теоретическая_эффективность": f"{theoretical_speedup / threads:.6f}",
                    "отклонение_ускорения_проц": f"{deviation:.2f}",
                    "альфа_подбора": f"{alpha:.2f}",
                }
            )

    print(f"Проверено: по {REPEATS} измерений для p=1..16.")
    print(
        f"Подбор α по средним ускорениям для p=1..{FIT_MAX_THREADS}: "
        f"α={alpha:.2f}, RMSE={rmse:.4f}."
    )
    print("Сводная таблица записана в results.csv.")


if __name__ == "__main__":
    main()
