import csv
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.size'] = 12

alpha = 0.62

def amdahl_speedup(p, a):
    return 1.0 / ((1 - a) + a / p)

def read_csv(path):
    with open(path) as f:
        header = f.readline().strip()
        sep = ';' if ';' in header else ','
        f.seek(0)
        return list(csv.reader(f, delimiter=sep))[1:]

# ---- График 1: время от N ----
Ns, Ts = [], []
for row in read_csv('time_vs_n.csv'):
    Ns.append(int(row[0]))
    Ts.append(float(row[1]))

plt.figure(figsize=(8, 5))
plt.plot(Ns, Ts, 'o-', color='steelblue', markersize=8, linewidth=2)
plt.xlabel('Размер массива N')
plt.ylabel('Время, с')
plt.title('Зависимость времени от размера массива (1 поток)')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('graph1_time_vs_n.png', dpi=150)
plt.close()

# ---- График 2: сравнения от N ----
Ns, Cs = [], []
for row in read_csv('cmp_vs_n.csv'):
    Ns.append(int(row[0]))
    Cs.append(int(row[1]))

plt.figure(figsize=(8, 5))
plt.plot(Ns, Cs, 'o-', color='seagreen', markersize=8, linewidth=2, label='Эксперимент')
plt.plot(Ns, Ns, '--', color='gray', linewidth=1.5, label='Теория: y = N')
plt.xlabel('Размер массива N')
plt.ylabel('Число сравнений')
plt.title('Зависимость числа сравнений от размера массива (1 поток)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('graph2_cmp_vs_n.png', dpi=150)
plt.close()

# ---- Графики 3 и 4: ускорение и эффективность по mean и min ----
ps, means, mins = [], [], []
for row in read_csv('time_vs_p.csv'):
    ps.append(int(row[0]))
    means.append(float(row[1]))
    mins.append(float(row[2]))

t1_mean = means[0]
t1_min  = mins[0]

S_mean = [t1_mean / t for t in means]
S_min  = [t1_min / t for t in mins]
E_mean = [S_mean[i] / ps[i] for i in range(len(ps))]
E_min  = [S_min[i] / ps[i] for i in range(len(ps))]

S_theor = [amdahl_speedup(p, alpha) for p in ps]
E_theor = [S_theor[i] / ps[i] for i in range(len(ps))]

# График 3: ускорение
plt.figure(figsize=(9, 5.5))
plt.plot(ps, S_mean, 's-', color='orange', markersize=7, linewidth=2,
         label='Эксперимент (среднее)')
plt.plot(ps, S_min, 'o-', color='blue', markersize=7, linewidth=2,
         label='Эксперимент (минимум)')
#plt.plot(ps, ps, ':', color='gray', linewidth=1.5,
#         label='Идеальное ускорение S(p) = p')
plt.plot(ps, S_theor, '--', color='darkred', linewidth=2,
         label=f'Теория (Амдал, α={alpha})')
plt.xlabel('Число потоков p')
plt.ylabel('Ускорение S(p)')
plt.title('Сравнение экспериментального и теоретического ускорения')
plt.legend()
plt.grid(True, alpha=0.3)
plt.xticks(ps)
plt.tight_layout()
plt.savefig('graph3_speedup.png', dpi=150)
plt.close()

# График 4: эффективность
plt.figure(figsize=(9, 5.5))
plt.plot(ps, E_mean, 's-', color='orange', markersize=7, linewidth=2,
         label='Эксперимент (среднее)')
plt.plot(ps, E_min, 'o-', color='blue', markersize=7, linewidth=2,
         label='Эксперимент (минимум)')
#plt.axhline(y=1.0, color='gray', linestyle=':', linewidth=1.5,
#            label='Идеальная эффективность E(p) = 1')
plt.plot(ps, E_theor, '--', color='chocolate', linewidth=2,
         label=f'Теория (Амдал, α={alpha})')
plt.xlabel('Число потоков p')
plt.ylabel('Эффективность E(p)')
plt.title('Сравнение экспериментальной и теоретической эффективности')
plt.legend()
plt.grid(True, alpha=0.3)
plt.xticks(ps)
plt.tight_layout()
plt.savefig('graph4_efficiency.png', dpi=150)
plt.close()

print("Готово: graph1..graph4.png")
print()
print(f"{'p':>3} | {'T_mean':>10} | {'T_min':>10} | {'S_mean':>7} | {'S_min':>7} | {'E_mean':>7} | {'E_min':>7}")
print("-" * 72)
for i, p in enumerate(ps):
    print(f"{p:>3} | {means[i]:>10.6f} | {mins[i]:>10.6f} | "
          f"{S_mean[i]:>7.3f} | {S_min[i]:>7.3f} | "
          f"{E_mean[i]:>7.3f} | {E_min[i]:>7.3f}")