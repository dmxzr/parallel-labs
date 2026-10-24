import csv
import matplotlib
matplotlib.use('Agg')
import numpy as np
import matplotlib.pyplot as plt


def read_csv(path):
    with open(path, newline='') as f:
        header = f.readline().strip()
        sep = ';' if ';' in header else ','
        f.seek(0)
        rows = list(csv.reader(f, delimiter=sep))
    if not rows:
        return []
    return rows[1:]


def parse_speedup_csv(path):
    rows = read_csv(path)
    ps, mins = [], []
    for row in rows:
        if len(row) < 2:
            continue
        ps.append(int(row[0]))
        mins.append(float(row[2]))
    return np.array(ps, dtype=float), np.array(mins, dtype=float)


# Experimental curve from CSV, same style as other plots: points + connected line
ps, t_min = parse_speedup_csv('time_vs_p.csv')
t1 = t_min[0]
S_exp = np.array([t1 / t for t in t_min], dtype=float)

# Piecewise theoretical curves selected for the three segments

def S1(p):
    return 3.25 * p / (p + 1.9)


def S2(p):
    return 2.0 - 0.1 / (p + 1.0)


def S3(p):
    return 1.7 - 0.05 * np.log(p)


def rmse(observed, predicted):
    return np.sqrt(np.mean((observed - predicted) ** 2))

# Build the piecewise theoretical curve over full p range
p_grid = np.linspace(1, 16, 1000)
S_piece = np.empty_like(p_grid)
for i, p in enumerate(p_grid):
    if p <= 4:
        S_piece[i] = S1(p)
    elif p <= 8:
        S_piece[i] = S2(p)
    else:
        S_piece[i] = S3(p)

# RMSE per segment
seg1 = ps[(ps >= 1) & (ps <= 4)]
seg2 = ps[(ps >= 5) & (ps <= 8)]
seg3 = ps[(ps >= 9) & (ps <= 16)]
exp1 = S_exp[(ps >= 1) & (ps <= 4)]
exp2 = S_exp[(ps >= 5) & (ps <= 8)]
exp3 = S_exp[(ps >= 9) & (ps <= 16)]

print(f"RMSE segment 1 [1,4]: {rmse(exp1, S1(seg1)):.4f}")
print(f"RMSE segment 2 [5,8]: {rmse(exp2, S2(seg2)):.4f}")
print(f"RMSE segment 3 [9,16]: {rmse(exp3, S3(seg3)):.4f}")

# Plot: experimental data as connected curve with markers
plt.figure(figsize=(9, 5.5))
plt.plot(ps, S_exp, 'o-', color='royalblue', markersize=7, linewidth=2, label='Эксперимент')
plt.plot(p_grid, S_piece, '-', color='gray', linewidth=2.2, alpha=0.5, label='Кусочная теоретическая модель')

# Highlight the three regimes
plt.axvspan(1, 4, color='lightgray', alpha=0.15)
plt.axvspan(5, 8, color='gray', alpha=0.10)
plt.axvspan(9, 16, color='darkgray', alpha=0.10)

# Theoretical curves on their natural ranges
p1 = np.linspace(1, 4, 200)
p2 = np.linspace(5, 8, 200)
p3 = np.linspace(9, 16, 200)

plt.plot(p1, S1(p1), '--', color='darkorange', linewidth=1.8, alpha=0.9, label='Участок 1: S1(p)')
plt.plot(p2, S2(p2), '--', color='forestgreen', linewidth=1.8, alpha=0.9, label='Участок 2: S2(p)')
plt.plot(p3, S3(p3), '--', color='purple', linewidth=1.8, alpha=0.9, label='Участок 3: S3(p)')

plt.xlabel('Число потоков p')
plt.ylabel('Ускорение S(p)')
plt.title('Экспериментальное ускорение и кусочно-аппроксимирующие теоретические кривые')
plt.grid(True, alpha=0.3)
plt.xticks(ps)
plt.legend(loc='best')
plt.tight_layout()
plt.savefig('graph5_three_regimes.png', dpi=150)
#plt.show()

