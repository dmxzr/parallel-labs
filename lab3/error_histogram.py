#!/usr/bin/env python3
"""Гистограмма частот максимальной ошибки решения СЛАУ (1700 измерений).

Данные: raw_measurements.csv (столбец "Макс_ошибка").
По данным все 1700 значений совпадают (5.950795411991e-14), поэтому гистограмма
вырождается в один столбец; ось X логарифмическая, чтобы показать одновременно
пик ошибки и допуск 1e-6 из программы.

Скрипт переносим (Linux/macOS): пути к данным и шрифтам ищутся автоматически.
Зависимости: matplotlib, numpy. Seaborn и Pillow необязательны.
"""
import collections
import csv
import os
import sys

import matplotlib
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False

# ── Пути: данные ищем рядом со скриптом и в текущем каталоге ──
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_CANDIDATES = [
    os.path.join(SCRIPT_DIR, 'raw_measurements.csv'),
    os.path.join(SCRIPT_DIR, 'results', 'raw_measurements.csv'),
    os.path.join(os.getcwd(), 'raw_measurements.csv'),
    os.path.join(os.getcwd(), 'results', 'raw_measurements.csv'),
]
SRC = next((p for p in DATA_CANDIDATES if os.path.exists(p)), None)
if SRC is None:
    sys.exit('Не найден raw_measurements.csv. Положите файл рядом со скриптом '
             'или запустите скрипт из каталога с данными.')
OUT = os.path.join(SCRIPT_DIR, 'error_histogram.png')

ACCENT = '#1769aa'  # цвет акцентов отчёта lab3_report
TOLERANCE = 1e-6    # допуск из check_solution (lab3.cpp)

# ── Шрифты: регистрируем первый найденный; если ни одного нет, остаётся
#    встроенный в matplotlib DejaVu Sans (он и так знает кириллицу) ──
FONT_CANDIDATES = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',            # Linux
    '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',       # macOS
    '/System/Library/Fonts/Supplemental/Arial.ttf',               # macOS
    os.path.join(os.path.dirname(matplotlib.__file__),
                 'mpl-data', 'fonts', 'ttf', 'DejaVuSans.ttf'),   # в составе matplotlib
]
for font_path in FONT_CANDIDATES:
    if os.path.exists(font_path):
        try:
            fm.fontManager.addfont(font_path)
        except Exception as error:
            print(f'Шрифт {font_path} не зарегистрирован: {error}')
        break

RC = {
    'axes.unicode_minus': False,
    'font.family': 'sans-serif',
    'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica'],
    'figure.facecolor': '#FFFFFF',
    'axes.facecolor': '#FFFFFF',
    'axes.edgecolor': '#E5E7EB',
    'axes.linewidth': 0.8,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'grid.color': '#F3F4F6',
    'grid.alpha': 0.5,
    'grid.linewidth': 0.5,
    'xtick.major.size': 0,
    'ytick.major.size': 0,
    'axes.titlesize': 16,
    'axes.titleweight': 'bold',
    'axes.titlepad': 16,
    'legend.frameon': False,
    'figure.dpi': 200,
    'savefig.dpi': 300,
}
if HAS_SEABORN:
    sns.set_theme(style='whitegrid', font='DejaVu Sans', rc=RC)
else:
    plt.rcParams.update(RC)

values = []
with open(SRC, encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        values.append(float(row['Макс_ошибка']))

counter = collections.Counter(values)
unique = sorted(counter)
n = len(values)
err = unique[0]
print(f'Данные: {SRC}')
print(f'Измерений: {n}')
print(f'Уникальных значений: {len(unique)}: {[f"{v:.6e}" for v in unique]}')
print(f'Частоты: {dict(counter)}')
print(f'Допуск/ошибка = {TOLERANCE / err:.3e} (порядков: {np.log10(TOLERANCE / err):.2f})')

fig, ax = plt.subplots(figsize=(11, 6), constrained_layout=True)

# Декадные корзины от 1e-15 до 1e-4: значение попадает в корзину [1e-14, 1e-13]
bins = np.logspace(-15, -4, 12)
counts, edges = np.histogram(values, bins=bins)
nonzero = counts > 0
print(f'Корзины с данными: {[(f"{edges[i]:.0e}", f"{edges[i+1]:.0e}", int(counts[i])) for i in range(len(counts)) if counts[i]]}')

ax.hist(values, bins=bins, color=ACCENT, alpha=0.85, edgecolor='white', linewidth=1.0, zorder=3)
ax.set_xscale('log')
ax.set_xlim(1e-15, 1e-4)
ax.set_ylim(0, n * 1.18)

# Допуск из программы
ax.axvline(TOLERANCE, color='#CC3311', linestyle='--', linewidth=1.8, zorder=2)
ax.text(TOLERANCE * 0.55, n * 0.55, 'допуск из программы\n$10^{-6}$',
        ha='right', va='center', fontsize=12, color='#CC3311')

# Подпись единственного столбца
bin_lo, bin_hi = 1e-14, 1e-13
ax.annotate(f'все {n} измерений:\n$5.9508\\cdot 10^{{-14}}$',
            xy=(np.sqrt(bin_lo * bin_hi), counts[nonzero][0]),
            xytext=(2.2e-12, n * 0.92),
            fontsize=12, color='#243447', ha='left', va='top',
            arrowprops=dict(arrowstyle='->', color='#64748B', lw=1.2))

ax.set_title('Ошибка решения детерминирована: все 1700 измерений дают\n'
             'одну и ту же максимальную ошибку $5.95\\cdot 10^{-14}$ при допуске $10^{-6}$',
             loc='left')
ax.set_xlabel('Максимальная покомпонентная ошибка $\\max_i\\,|x_i - x_{ref,i}|$', fontsize=13)
ax.set_ylabel('Частота (число измерений)', fontsize=13)
ax.set_xticks([1e-15, 1e-14, 1e-13, 1e-12, 1e-11, 1e-10, 1e-9, 1e-8, 1e-7, 1e-6, 1e-5, 1e-4])
ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))

fig.savefig(OUT, dpi=300, facecolor='white')
plt.close(fig)

# Проверка файла (Pillow необязательна)
print(f'Файл сохранён: {OUT}; вес {os.path.getsize(OUT)} байт.')
try:
    from PIL import Image
    im = Image.open(OUT).convert('L')
    h = im.histogram()
    print(f'Размер {im.size}; доля не-белого: {1 - h[255] / sum(h):.4f}')
except ImportError:
    pass
