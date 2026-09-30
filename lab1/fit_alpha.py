import csv
import numpy as np
import matplotlib.pyplot as plt

def amdahl(p, a):
    return 1.0 / ((1 - a) + a / p)

def read_csv(path):
    with open(path) as f:
        header = f.readline().strip()
        sep = ';' if ';' in header else ','
        f.seek(0)
        return list(csv.reader(f, delimiter=sep))[1:]

# Читаем времена
ps, mins = [], []
for row in read_csv('time_vs_p.csv'):
    ps.append(int(row[0]))
    mins.append(float(row[2]))   # min — колонка 3 (индекс 2)

t1 = mins[0]
S_exp = [t1 / t for t in mins]

# Перебираем alpha от 0.1 до 0.99
alphas = np.arange(0.10, 0.99, 0.01)
best_alpha = None
best_rmse = 1e9
results = []

# Подбираем только по точкам p=1..8 (где Амдал имеет смысл)
mask = [i for i, p in enumerate(ps) if p <= 8]

for a in alphas:
    S_theor = [amdahl(p, a) for p in ps]
    # RMSE только по p<=8
    errs = [(S_exp[i] - S_theor[i])**2 for i in mask]
    rmse = np.sqrt(np.mean(errs))
    results.append((a, rmse))
    if rmse < best_rmse:
        best_rmse = rmse
        best_alpha = a

print(f"Лучшее alpha = {best_alpha:.2f}, RMSE = {best_rmse:.4f}")
print()
print(f"{'alpha':>6} | {'RMSE':>8}")
print("-" * 18)
for a, r in results[::5]:   # каждое пятое значение
    print(f"{a:>6.2f} | {r:>8.4f}")

# Финальный график
S_theor_best = [amdahl(p, best_alpha) for p in ps]

plt.figure(figsize=(9, 5.5))
plt.plot(ps, S_exp, 'o-', color='crimson', markersize=7, linewidth=2,
         label='Эксперимент (min)')
plt.plot(ps, ps, ':', color='gray', linewidth=1.5,
         label='Идеальное S(p) = p')
plt.plot(ps, S_theor_best, '--', color='darkred', linewidth=2,
         label=f'Амдал при α = {best_alpha:.2f}')
plt.xlabel('Число потоков p')
plt.ylabel('Ускорение S(p)')
plt.title(f'Подбор α методом наименьших квадратов: α = {best_alpha:.2f}')
plt.legend()
plt.grid(True, alpha=0.3)
plt.xticks(ps)
plt.tight_layout()
plt.savefig('graph3_speedup.png', dpi=150)
plt.close()

# Таблица отклонений для лучшего alpha
print()
print("Сравнение при лучшем alpha:")
print(f"{'p':>3} | {'S_exp':>8} | {'S_theor':>8} | {'delta, %':>9}")
print("-" * 40)
for i, p in enumerate(ps):
    delta = abs(S_exp[i] - S_theor_best[i]) / S_theor_best[i] * 100
    print(f"{p:>3} | {S_exp[i]:>8.3f} | {S_theor_best[i]:>8.3f} | {delta:>9.1f}")