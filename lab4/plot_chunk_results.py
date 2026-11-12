#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Построение защитного графика из CSV-таблицы dyn_chunk_bench.

Использование:
    python3 plot_chunk_results.py [csv] [-o out.png]

CSV ожидается в формате dyn_chunk_bench.cpp:
    # threads = T, N = N, reps = R
    kind,chunk,min_ms,median_ms,sum
    ...

Скрипт автоматически:
  - парсит CSV (без pandas, только stdlib + matplotlib);
  - находит лучший dynamic и оптимальное окно (+1% к лучшему);
  - оценивает накладные расходы на выдачу порции и работу итерации;
  - строит график «время vs chunk»: линии dynamic/static, подсветка окна,
    аннотации штрафа за chunk=1 и деградации при слишком крупных порциях.
"""
import argparse
import csv
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# DejaVu Sans поставляется вместе с matplotlib — работает на macOS без установки шрифтов.
plt.rcParams.update({
    'font.sans-serif': ['DejaVu Sans'],
    'axes.unicode_minus': False,
    'figure.facecolor': '#FFFFFF',
    'axes.facecolor': '#FFFFFF',
    'axes.edgecolor': '#E5E7EB',
    'axes.linewidth': 0.8,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.grid': False,
    'xtick.major.size': 0,
    'ytick.major.size': 0,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 15,
    'axes.titleweight': 'bold',
    'axes.titlepad': 16,
    'legend.frameon': False,
    'legend.fontsize': 10,
    'figure.dpi': 200,
    'savefig.dpi': 200,
    'savefig.facecolor': '#FFFFFF',
})

BLUE, G400, G300 = '#0077BB', '#9CA3AF', '#D1D5DB'


def load(path):
    """Читает CSV; возвращает (rows, threads, n, reps)."""
    rows, threads, n, reps = [], None, None, None
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('#'):
                for part in line.lstrip('# ').split(','):
                    key, _, val = part.partition('=')
                    key, val = key.strip(), val.strip()
                    if key == 'threads':
                        threads = int(val)
                    elif key == 'N':
                        n = int(val)
                    elif key == 'reps':
                        reps = int(val)
                continue
            parts = line.split(',')
            if parts[0] in ('kind', 'schedule'):
                continue
            rows.append((parts[0], int(parts[1]), float(parts[3])))
    return rows, threads, n, reps


def main():
    ap = argparse.ArgumentParser(description='График из CSV-результатов dyn_chunk_bench')
    ap.add_argument('csv', nargs='?', default='dyn_chunk_results.csv')
    ap.add_argument('-o', '--out', default='dyn_chunk_results.png')
    args = ap.parse_args()

    rows, threads, n, reps = load(args.csv)
    if threads is None or n is None:
        raise SystemExit('В CSV нет строки "# threads = ..., N = ..." — не могу подписать график')

    static = {c: m for k, c, m in rows if k == 'static'}
    dyn = {c: m for k, c, m in rows if k == 'dynamic'}
    if not dyn:
        raise SystemExit('В CSV нет строк kind=dynamic')

    best_chunk, best_time = min(dyn.items(), key=lambda kv: kv[1])
    window = [c for c, m in dyn.items() if m <= best_time * 1.01]
    wlo, whi = min(window), max(window)

    static_med = sorted(static.values())[len(static) // 2] if static else None
    overhead_ns = (dyn[1] - best_time) * 1e6 / n if 1 in dyn else None
    per_iter_ns = best_time * 1e6 / n * threads
    chunk_max_10x = n // (10 * threads)

    # Консольная сводка (тоже полезна для защиты)
    print(f'Потоков: {threads}, N = {n}, reps = {reps}')
    print(f'Лучший dynamic: chunk={best_chunk} -> {best_time:.1f} мс')
    print(f'Оптимальное окно (+1% к лучшему): chunk = {wlo}..{whi}')
    if static_med:
        print(f'Медиана static: {static_med:.1f} мс '
              f'(лучший dynamic на {(static_med - best_time) / static_med * 100:+.1f}%)')
    if overhead_ns:
        print(f'Оценки: выдача порции ~{overhead_ns:.0f} нс, итерация ~{per_iter_ns:.0f} нс/поток')
    print(f'Верхняя граница по правилу "порций >= 10 x потоков": chunk <= {chunk_max_10x}')

    # ── График ──
    fig, ax = plt.subplots(figsize=(11, 6), constrained_layout=True)
    xs = sorted(dyn)
    ys = [dyn[c] for c in xs]

    ax.axvspan(wlo, whi, color='#EFF6FF', zorder=1)
    ax.plot(xs, ys, color=BLUE, linewidth=2.5, marker='o', markersize=6,
            markerfacecolor='white', markeredgewidth=2, markeredgecolor=BLUE,
            zorder=3, label='schedule(dynamic, chunk)')
    if static_med:
        ax.axhline(static_med, color=G400, linewidth=1.5, linestyle='--', zorder=2,
                   label='static (медиана)')

    # Подписи оси X: главные метки разрежены по лог-зазору, минорные — без подписей
    ax.set_xscale('log', base=2)
    major = [xs[0]]
    for c in xs[1:]:
        if __import__('math').log2(c / major[-1]) >= 1.9:
            major.append(c)
    if xs[-1] not in major:
        major[-1] = xs[-1]          # последний пункт всегда подписан
    ax.set_xticks(major)
    minor = [c for c in xs if c not in major]
    ax.set_xticks(minor, minor=True)
    ax.xaxis.set_minor_formatter(mticker.NullFormatter())
    ax.set_xticklabels([f'{v:,}'.replace(',', ' ') for v in major])
    ax.tick_params(axis='x', which='minor', length=0)
    ax.set_xlabel('Размер порции chunk (лог. шкала)')
    ax.set_ylabel(f'Время, мс (медиана {reps or "?"} прогонов)')

    # Аннотации, позиции подбираются от данных — без наложения
    ax.set_ylim(min(ys) * 0.92, max(ys) * 1.22)
    x_text_left = xs[min(3, len(xs) - 1)]
    if 1 in dyn and overhead_ns:
        ax.annotate(f'chunk=1: +{(dyn[1] - best_time) / best_time * 100:.0f}% —\n'
                    ,
                    xy=(1, dyn[1]), xytext=(1.6, dyn[1] * 1.04),
                    fontsize=10, color='#111827',
                    arrowprops=dict(arrowstyle='->', color='#9CA3AF', lw=1.0))
    ax.text(wlo * 1.15, max(ys) * 1.13, f'оптимальное окно:\nchunk {wlo} - {whi}',
            fontsize=10, color='#374151', ha='left', va='top')

    # Деградация справа: точка максимума среди chunk > whi
    big = {c: m for c, m in dyn.items() if c > whi}
    if big:
        wc, wt = max(big.items(), key=lambda kv: kv[1])
        nchunks = -(-n // wc)
       
    ax.set_title('schedule(dynamic): время vs размер порции chunk', loc='left')
    ax.set_title(f'{threads} потоков, N = {n:,}'.replace(',', ' '),
                 loc='right', fontsize=11, color='#6B7280', fontweight='normal')
    ax.yaxis.grid(True, alpha=0.08, color=G300)
    ax.set_axisbelow(True)
    ax.legend(loc='upper right', bbox_to_anchor=(1.0, 1.0))

    fig.savefig(args.out, dpi=200, facecolor='white')
    plt.close(fig)

    from PIL import Image
    try:
        im = Image.open(args.out).convert('L')
        h = im.histogram()
        print(f'Chart: {os.path.abspath(args.out)} {im.size}, '
              f'non-white ratio {1 - h[255] / sum(h):.3f}')
    except Exception:
        print(f'Chart saved: {os.path.abspath(args.out)} '
              f'({os.path.getsize(args.out)} bytes)')


if __name__ == '__main__':
    main()
