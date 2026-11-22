#!/usr/bin/env python3
import csv
from pathlib import Path
from statistics import mean

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
COLUMNS = ["mode", "p", "mean_s", "speedup_mean", "efficiency_mean"]


def read_csv(name):
    with (ROOT / name).open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def summarize(rows):
    by_p = {}
    for row in rows:
        by_p.setdefault(int(row["p"]), []).append(float(row["time_s"]))
    return [(p, mean(times)) for p, times in sorted(by_p.items())]


def metrics(mode, stats):
    _, mean1 = stats[0]
    for p, mean_p in stats:
        speedup = mean1 / mean_p
        yield dict(zip(COLUMNS, (mode, p, mean_p, speedup, speedup / p)))


def draw_graph(series, field, label, filename, scale=1,
               x_label="Число потоков OpenMP или процессов MPI"):
    fig, ax = plt.subplots(figsize=(8, 4.6), layout="constrained")
    for name, rows, color in series:
        ps = [row["p"] for row in rows]
        ax.plot(ps, [row[field] * scale for row in rows], "o-",
                color=color, markersize=4, label=name)
    ax.set_xlabel(x_label)
    ax.set_ylabel(label)
    ax.set_xticks(range(1, 17))
    ax.grid(alpha=0.3)
    if series:
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=2, fontsize=9)
    fig.savefig(ROOT / filename, dpi=150)
    plt.close(fig)


def main():
    linux = read_csv("omp_lab1_linux.csv")
    linux_stats = [(int(row["p"]), float(row["mean"])) for row in linux]
    linux_rows = list(metrics("omp_lab1_linux", linux_stats))

    omp = read_csv("omp_measurements.csv") if (ROOT / "omp_measurements.csv").exists() else []
    mpi = read_csv("mpi_measurements.csv") if (ROOT / "mpi_measurements.csv").exists() else []
    if omp and mpi and {row["max"] for row in omp} != {row["max"] for row in mpi}:
        raise RuntimeError("Результаты поиска MPI и OpenMP различаются")

    series = []
    if omp:
        omp_macos = ("OpenMP, macOS", list(metrics("omp_macos", summarize(omp))), "darkorange")
        series.append(omp_macos)
        draw_graph(
            [("OpenMP, Linux (ЛР № 1)", linux_rows, "steelblue"), omp_macos],
            "mean_s", "Среднее время, мс", "graph0_openmp_platforms.png",
            scale=1000, x_label="Число потоков OpenMP",
        )
    if mpi:
        series.append(("MPI, macOS",
                       list(metrics("mpi_macos", summarize(mpi))), "seagreen"))

    with (ROOT / "results.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        for rows in [linux_rows] + [rows for _, rows, _ in series]:
            writer.writerows({key: f"{value:.9f}" if isinstance(value, float) else value
                              for key, value in row.items()} for row in rows)

    draw_graph(series, "mean_s", "Среднее время, мс", "graph1_time_vs_p.png", scale=1000)
    draw_graph(series, "speedup_mean", "Ускорение", "graph2_speedup.png")
    draw_graph(series, "efficiency_mean", "Эффективность, %", "graph3_efficiency.png", scale=100)


if __name__ == "__main__":
    main()
