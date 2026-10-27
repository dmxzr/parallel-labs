#!/usr/bin/env python3
import csv
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.abspath(__file__))


def read_results():
    with open(
        os.path.join(ROOT, "results.csv"), newline="", encoding="utf-8"
    ) as file:
        return list(csv.DictReader(file))


def main():
    plt.rcParams["font.family"] = "DejaVu Sans"
    rows = read_results()
    threads = [int(row["потоки"]) for row in rows]
    experimental_time = [
        float(row["экспериментальное_время_среднее_с"]) for row in rows
    ]
    experimental_speedup = [
        float(row["экспериментальное_ускорение"]) for row in rows
    ]
    experimental_efficiency = [
        float(row["экспериментальная_эффективность"]) for row in rows
    ]
    theoretical_speedup = [
        float(row["теоретическое_ускорение"]) for row in rows
    ]
    theoretical_efficiency = [
        float(row["теоретическая_эффективность"]) for row in rows
    ]
    alpha = float(rows[0]["альфа_подбора"])

    plots = [
        (
            "graph1_time_vs_p.png",
            "Среднее время выполнения по числу потоков",
            "Среднее время, с",
            [
                (experimental_time, "-", "Экспериментальное время"),
            ],
        ),
        (
            "graph2_speedup.png",
            "Ускорение по числу потоков",
            "Ускорение",
            [
                (experimental_speedup, "-", "Экспериментальное ускорение"),
                (theoretical_speedup, "--", f"Модель Амдала (α = {alpha:.2f})"),
            ],
        ),
        (
            "graph3_efficiency.png",
            "Эффективность по числу потоков",
            "Эффективность",
            [
                (experimental_efficiency, "-", "Экспериментальная эффективность"),
                (
                    theoretical_efficiency,
                    "--",
                    f"Модель Амдала (α = {alpha:.2f})",
                ),
            ],
        ),
    ]

    for filename, title, ylabel, curves in plots:
        fig, ax = plt.subplots(figsize=(9, 5.5))
        for values, style, label in curves:
            ax.plot(threads, values, linestyle=style, marker="o", label=label)
        ax.set_title(title)
        ax.set_xlabel("Число потоков")
        ax.set_ylabel(ylabel)
        ax.set_xticks(threads)
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.legend()
        fig.tight_layout()
        fig.savefig(os.path.join(ROOT, filename), dpi=160)
        plt.close(fig)

    print("Графики построены.")


if __name__ == "__main__":
    main()
