#!/usr/bin/env python3
import argparse
import csv
import io
import math
import os
import shlex
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Sequence, Tuple

from fit_amdahl import fit_amdahl_model, overhead_speedup, theoretical_speedup


THREAD_COUNTS = list(range(1, 17))
RAW_COLUMNS = [
    "Тип",
    "Потоки",
    "Повтор",
    "Прямой_ход_с",
    "Обратный_ход_с",
    "Общее_время_с",
    "Макс_ошибка",
]


def build_program(source: Path, binary: Path) -> None:
    compiler = shlex.split(os.environ.get("CXX", "clang++" if sys.platform == "darwin" else "g++"))
    command = compiler + ["-std=c++17", "-O2"]
    if sys.platform == "darwin":
        omp_prefix = Path("/opt/homebrew/opt/libomp")
        if not omp_prefix.exists():
            omp_prefix = Path("/usr/local/opt/libomp")
        if not omp_prefix.exists():
            raise RuntimeError("Не найдена libomp. Установите OpenMP runtime.")
        command += [
            "-Xpreprocessor",
            "-fopenmp",
            f"-I{omp_prefix / 'include'}",
            str(source),
            f"-L{omp_prefix / 'lib'}",
            "-lomp",
            "-o",
            str(binary),
        ]
    else:
        command += ["-fopenmp", str(source), "-o", str(binary)]
    subprocess.run(command, check=True)


def run_program(binary: Path, size: int, repeats: int) -> List[dict]:
    result = subprocess.run(
        [str(binary), str(size), str(repeats)],
        check=True,
        capture_output=True,
        text=True,
    )
    rows = list(csv.DictReader(io.StringIO(result.stdout)))
    expected_count = repeats * (len(THREAD_COUNTS) + 1)
    if len(rows) != expected_count:
        raise RuntimeError(f"Ожидалось {expected_count} измерений, получено {len(rows)}.")

    configurations = {(row["Тип"], int(row["Потоки"])) for row in rows}
    expected_configurations = {("serial", 1)} | {
        ("parallel", threads) for threads in THREAD_COUNTS
    }
    if configurations != expected_configurations:
        raise RuntimeError("В измерениях отсутствуют некоторые режимы или потоки.")
    counts = {}
    for row in rows:
        key = (row["Тип"], int(row["Потоки"]))
        counts[key] = counts.get(key, 0) + 1
    if any(count != repeats for count in counts.values()):
        raise RuntimeError("Число повторов для некоторых режимов не совпадает с заданным.")
    if any(float(row["Макс_ошибка"]) >= 1e-6 for row in rows):
        raise RuntimeError("Проверка точности не пройдена хотя бы в одном измерении.")
    return rows


def write_raw_csv(path: Path, rows: Sequence[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=RAW_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def write_summary_csv(path: Path, results: Sequence[dict], alpha: float) -> None:
    columns = [
        "Потоки",
        "Последовательное время, с",
        "Параллельное время, с",
        "Стандартное отклонение времени, с",
        "Прямой ход, с",
        "Обратный ход, с",
        "Экспериментальное ускорение",
        "Ускорение с накладными расходами",
        "Экспериментальная эффективность",
        "Доля параллельной части α",
        "Коэффициент накладных расходов β",
    ]
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        for row in results:
            writer.writerow(
                {
                    "Потоки": row["threads"],
                    "Последовательное время, с": f'{row["serial_total"]:.9f}',
                    "Параллельное время, с": f'{row["total"]:.9f}',
                    "Стандартное отклонение времени, с": f'{row["total_sd"]:.9f}',
                    "Прямой ход, с": f'{row["forward"]:.9f}',
                    "Обратный ход, с": f'{row["back"]:.9f}',
                    "Экспериментальное ускорение": f'{row["speedup"]:.6f}',
                    "Ускорение с накладными расходами": f'{row["overhead_speedup"]:.6f}',
                    "Экспериментальная эффективность": f'{row["efficiency"]:.6f}',
                    "Доля параллельной части α": f"{alpha:.12f}",
                    "Коэффициент накладных расходов β": f"{row['overhead']:.6f}",
                }
            )


def write_chart(
    path: Path,
    title: str,
    y_label: str,
    threads: List[int],
    series: Sequence[Tuple[str, Sequence[float], str]],
) -> None:
    width, height = 960, 600
    left, right, top, bottom = 105, 35, 75, 90
    plot_width = width - left - right
    plot_height = height - top - bottom
    all_values = [value for _, values, _ in series for value in values]
    max_value = max(all_values) * 1.1 if all_values else 1.0
    max_value = max(max_value, 1e-9)

    def x_pos(index: int) -> float:
        return left + index * plot_width / (len(threads) - 1)

    def y_pos(value: float) -> float:
        return top + plot_height * (1.0 - value / max_value)

    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<g font-family="Arial, sans-serif" fill="#222">',
        f'<text x="{width / 2}" y="35" text-anchor="middle" font-size="21" font-weight="bold">{title}</text>',
    ]
    for tick in range(6):
        value = max_value * tick / 5
        y = y_pos(value)
        elements.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" stroke="#ddd"/>')
        elements.append(f'<text x="{left-12}" y="{y+5:.1f}" text-anchor="end" font-size="13">{value:.3g}</text>')

    for index, count in enumerate(threads):
        x = x_pos(index)
        elements.append(f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{height-bottom}" stroke="#f0f0f0"/>')
        elements.append(f'<text x="{x:.1f}" y="{height-bottom+24}" text-anchor="middle" font-size="12">{count}</text>')

    elements.extend(
        [
            f'<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" stroke="#333"/>',
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{height-bottom}" stroke="#333"/>',
            f'<text x="{left + plot_width/2}" y="{height-25}" text-anchor="middle" font-size="15">Количество потоков</text>',
            f'<text x="24" y="{top + plot_height/2}" text-anchor="middle" font-size="15" transform="rotate(-90 24 {top + plot_height/2})">{y_label}</text>',
        ]
    )

    legend_y = height - 58
    legend_step = plot_width / max(1, len(series))
    for series_index, (label, values, color) in enumerate(series):
        points = " ".join(f"{x_pos(i):.1f},{y_pos(v):.1f}" for i, v in enumerate(values))
        elements.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2.5"/>')
        for i, value in enumerate(values):
            elements.append(f'<circle cx="{x_pos(i):.1f}" cy="{y_pos(value):.1f}" r="3.5" fill="{color}"/>')
        legend_x = left + series_index * legend_step
        elements.append(f'<line x1="{legend_x}" y1="{legend_y}" x2="{legend_x+28}" y2="{legend_y}" stroke="{color}" stroke-width="3"/>')
        elements.append(f'<text x="{legend_x+36}" y="{legend_y+5}" font-size="13">{label}</text>')

    elements.extend(["</g>", "</svg>"])
    path.write_text("\n".join(elements), encoding="utf-8")


def summarize(rows: Sequence[dict]) -> Tuple[List[dict], float, float, int]:
    serial_times = [
        float(row["Общее_время_с"])
        for row in rows
        if row["Тип"] == "serial"
    ]
    serial_mean = statistics.mean(serial_times)
    if serial_mean <= 0 or not math.isfinite(serial_mean):
        raise RuntimeError("Некорректное время последовательного эталона.")

    results = []
    for threads in THREAD_COUNTS:
        samples = [
            row for row in rows
            if row["Тип"] == "parallel" and int(row["Потоки"]) == threads
        ]
        totals = [float(row["Общее_время_с"]) for row in samples]
        forward = statistics.mean(float(row["Прямой_ход_с"]) for row in samples)
        back = statistics.mean(float(row["Обратный_ход_с"]) for row in samples)
        total = statistics.mean(totals)
        speedup = serial_mean / total
        results.append(
            {
                "threads": threads,
                "serial_total": serial_mean,
                "forward": forward,
                "back": back,
                "total": total,
                "total_sd": statistics.stdev(totals) if len(totals) > 1 else 0.0,
                "speedup": speedup,
            }
        )

    alpha, overhead, fit_points = fit_amdahl_model(
        (row["threads"], row["speedup"]) for row in results
    )
    alpha = math.ceil(alpha * 1_000_000_000_000) / 1_000_000_000_000
    for row in results:
        fitted = overhead_speedup(row["threads"], alpha, overhead)
        row["overhead_speedup"] = fitted
        row["overhead"] = overhead
        row["efficiency"] = row["speedup"] / row["threads"]
        row["overhead_efficiency"] = fitted / row["threads"]
    return results, alpha, overhead, fit_points


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Сравнить последовательный и OpenMP-методы Гаусса, построить таблицу и графики."
    )
    parser.add_argument("--size", type=int, default=1000, help="размер матрицы (по умолчанию: 1000)")
    parser.add_argument("--repeats", type=int, default=7, help="повторы каждого режима (по умолчанию: 7)")
    args = parser.parse_args()
    if not 1 <= args.size <= 46340 or args.repeats < 2:
        parser.error("--size должен быть от 1 до 46340, а --repeats — не меньше 2")

    output_dir = Path(__file__).parent / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="lab3_benchmark_") as temporary_directory:
        binary = Path(temporary_directory) / "benchmark"
        try:
            build_program(Path(__file__).with_name("benchmark.cpp"), binary)
            rows = run_program(binary, args.size, args.repeats)
        except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
            print(f"Ошибка измерений: {error}", file=sys.stderr)
            return 1

    try:
        results, alpha, overhead, fit_points = summarize(rows)
    except (ValueError, RuntimeError) as error:
        print(f"Ошибка обработки результатов: {error}", file=sys.stderr)
        return 1

    write_raw_csv(output_dir / "raw_measurements.csv", rows)
    write_summary_csv(output_dir / "results.csv", results, alpha)
    threads = [row["threads"] for row in results]
    baseline = results[0]["serial_total"]
    write_chart(
        output_dir / "time.svg",
        f"Время решения системы, N = {args.size}",
        "Время, с",
        threads,
        [
            ("Параллельная версия", [row["total"] for row in results], "#1769aa"),
            ("Последовательный эталон", [baseline] * len(threads), "#555555"),
        ],
    )
    write_chart(
        output_dir / "speedup.svg",
        "Ускорение относительно последовательной версии",
        "Ускорение",
        threads,
        [
            ("Эксперимент", [row["speedup"] for row in results], "#1769aa"),
            ("Закон Амдала", [theoretical_speedup(count, alpha) for count in threads], "#2e7d32"),
        ],
    )
    write_chart(
        output_dir / "efficiency.svg",
        "Эффективность параллельных вычислений",
        "Эффективность",
        threads,
        [
            ("Эксперимент", [row["efficiency"] for row in results], "#1769aa"),
            (
                "Закон Амдала",
                [theoretical_speedup(count, alpha) / count for count in threads],
                "#2e7d32",
            ),
        ],
    )

    print(f"Матрица: {args.size} x {args.size}; повторов: {args.repeats}")
    print(f"Последовательный эталон (среднее): {baseline:.9f} с")
    print(f"Подобранная доля параллельной части: α = {alpha:.6f} ({alpha:.2%})")
    print(f"Подобранные накладные расходы: β = {overhead:.6f} на дополнительный поток")
    print(f"Кривая Амдала выше всех измерений p=2..16; учтено точек: {fit_points}.")
    print("Кривая с накладными расходами аппроксимирует замеры отдельно.")
    print(f"Лучшее ускорение: {max(results, key=lambda row: row['speedup'])['speedup']:.3f}x")
    print(f"Результаты сохранены в: {output_dir.resolve()}")
    print("Потоки | общее время, с | ± ст. откл. | ускорение | эффективность")
    for row in results:
        print(
            f'{row["threads"]:>6} | {row["total"]:>14.6f} | '
            f'{row["total_sd"]:>11.6f} | {row["speedup"]:>9.3f} | '
            f'{row["efficiency"]:>14.3f}'
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
