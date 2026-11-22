#!/usr/bin/env python3
import argparse
import csv
import hashlib
import io
import math
import os
import re
import shlex
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
N = 10_000_000
REPEATS = 100
WORKERS = range(1, 17)
COLUMNS = ["p", "N", "repeat", "max", "time_s"]


def default_build_dir():
    checkout = hashlib.sha256(os.fsencode(ROOT)).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / f"parallel-lab5-{os.getuid()}-{checkout}"


BUILD = Path(os.environ.get("LAB5_BUILD_DIR") or default_build_dir()).resolve()


def run_openmp():
    command = [str(BUILD / "omp_lab1"), str(N), "0"]
    env = {**os.environ, "OMP_DYNAMIC": "FALSE",
           "OMP_PLACES": "threads", "OMP_PROC_BIND": "TRUE",
           "OMP_THREAD_LIMIT": str(max(WORKERS))}

    def run_once(p):
        env["OMP_NUM_THREADS"] = str(p)
        output = subprocess.check_output(command, env=env, text=True)
        match = re.search(r"N=(\d+); threads=(\d+); Max=(-?\d+); Time=([\d.]+)", output)
        if not match or tuple(map(int, match.group(1, 2))) != (N, p):
            raise RuntimeError(f"Некорректный вывод OpenMP: {output}")
        return match.group(3, 4)

    for _ in range(3):
        run_once(4)

    for p in WORKERS:
        print(f"OpenMP: {p} потоков", flush=True)
        for repeat in range(1, REPEATS + 1):
            maximum, elapsed = run_once(p)
            yield dict(zip(COLUMNS, (p, N, repeat, maximum, elapsed)))


def run_mpi(launcher):
    for p in WORKERS:
        print(f"MPI: {p} процессов", flush=True)
        command = [*launcher, "-n", str(p), str(BUILD / "mpi_lab5"), str(N), str(REPEATS)]
        output = subprocess.check_output(command, text=True)
        reader = csv.DictReader(io.StringIO(output))
        rows = list(reader)
        if reader.fieldnames != COLUMNS or len(rows) != REPEATS:
            raise RuntimeError(f"Некорректный CSV для {p} процессов")
        for repeat, row in enumerate(rows, 1):
            if tuple(int(row[key]) for key in ("p", "N", "repeat")) != (p, N, repeat):
                raise RuntimeError(f"Некорректные параметры измерения: {row}")
            yield row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("omp", "mpi"))
    parser.add_argument("--launcher", default="mpirun")
    args = parser.parse_args()

    rows = list(run_openmp() if args.mode == "omp" else run_mpi(shlex.split(args.launcher)))
    times = [float(row["time_s"]) for row in rows]
    if any(not math.isfinite(time) or time <= 0 for time in times):
        raise RuntimeError("Обнаружено некорректное время измерения")
    if len({int(row["max"]) for row in rows}) != 1:
        raise RuntimeError("Максимумы различаются между прогонами")

    path = ROOT / f"{args.mode}_measurements.csv"
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Сохранено {len(rows)} измерений в {path.name}")


if __name__ == "__main__":
    main()
