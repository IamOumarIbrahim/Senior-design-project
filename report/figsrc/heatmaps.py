"""Heatmaps (serif): decision matrix, risk matrix, spec-to-verification traceability."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman'], 'mathtext.fontset': 'stix',
                     'font.size': 11, 'axes.linewidth': 0})
BLUES = LinearSegmentedColormap.from_list('b', ['#f6f8fb', '#cfe0fb', '#2f80ed', '#173f78'])
RISK = LinearSegmentedColormap.from_list('r', ['#e6f6ec', '#fff4e2', '#f5a524', '#d64545'])

# ---------------------------------------------------------------- decision matrix
crit = ['Accuracy', 'Speed', 'Privacy', 'Cost', 'Power, heat', 'Install', 'Complexity', 'Availability']
w = np.array([.20, .18, .15, .14, .12, .08, .07, .06])
alts = ['A  On-device detection', 'B  Cloud-streamed vision', 'C  Landmark rules', 'D  Vehicle/wearable signals', 'E  Smartphone app']
S = np.array([[4, 4, 5, 4, 3, 4, 3, 4],
              [5, 2, 1, 2, 4, 3, 2, 4],
              [2, 5, 5, 4, 4, 4, 4, 4],
              [2, 5, 4, 2, 5, 2, 2, 3],
              [3, 3, 3, 5, 2, 5, 3, 5]], float)
tot = S @ w
fig, ax = plt.subplots(figsize=(10.5, 3.6), dpi=220)
im = ax.imshow(S, cmap=BLUES, vmin=1, vmax=5, aspect='auto')
for i in range(S.shape[0]):
    for j in range(S.shape[1]):
        ax.text(j, i, int(S[i, j]), ha='center', va='center', color='white' if S[i, j] >= 4 else '#1b2430', fontsize=12)
ax.set_xticks(range(len(crit)), [f'{c}\n({int(x * 100)}%)' for c, x in zip(crit, w)], fontsize=10.5)
ax.set_yticks(range(len(alts)), alts)
ax.tick_params(length=0)
ax.xaxis.tick_top()
for i, t in enumerate(tot):
    ax.text(len(crit) - .35, i, f'{t:.2f}', ha='left', va='center', fontsize=12.5,
            fontweight='bold' if i == np.argmax(tot) else 'normal', color='#1b2430')
ax.text(len(crit) - .35, -0.95, 'Total', ha='left', va='center', fontsize=10.5, color='#5b6675')
ax.set_xlim(-.5, len(crit) + .3)
ax.add_patch(plt.Rectangle((-.5, -.5), len(crit), 1, fill=False, ec='#e58e0b', lw=2.2))
fig.tight_layout(); fig.savefig('../Figures/heat_decision.pdf'); plt.close(fig)

# ---------------------------------------------------------------- risk matrix
risks = {'R1': (4, 4, 'Data-collection delay'), 'R2': (3, 4, 'Poor generalisation'), 'R3': (3, 3, 'Slow or hot Pi'),
         'R4': (3, 2, 'Too few hard negatives'), 'R5': (2, 4, 'Consent delays'), 'R6': (3, 3, 'Supply delays'),
         'R7': (2, 2, 'Hailo compile issues'), 'R8': (2, 2, 'Map/POI access')}
L = np.arange(1, 6)
Z = np.outer(L, L)[::-1]
fig, ax = plt.subplots(figsize=(5.4, 4.6), dpi=220)
ax.imshow(Z, cmap=RISK, vmin=1, vmax=25, extent=(.5, 5.5, .5, 5.5), origin='upper')
cells = {}
for k, (l, i, _) in risks.items():
    cells.setdefault((l, i), []).append(k)
for (l, i), ks in cells.items():
    ax.text(l, i, '\n'.join(ks), ha='center', va='center', fontsize=11, color='#1b2430', fontweight='bold')
ax.set_xticks(L, ['Rare', 'Unlikely', 'Possible', 'Likely', 'Almost\ncertain'], fontsize=9)
ax.set_yticks(L, ['Minor', 'Low', 'Moderate', 'High', 'Severe'], fontsize=9)
ax.set_xlabel('Likelihood'); ax.set_ylabel('Impact')
ax.tick_params(length=0)
for v in np.arange(.5, 6, 1):
    ax.axhline(v, color='white', lw=2); ax.axvline(v, color='white', lw=2)
fig.tight_layout(); fig.savefig('../Figures/heat_risk.pdf'); plt.close(fig)

# ---------------------------------------------------------------- traceability
specs = [f'FS-{k:02d}' for k in range(1, 27)]
methods = ['Test', 'Analysis', 'Inspection', 'Demonstration']
M = np.zeros((4, 26))
prim = {1: 0, 2: 0, 3: 0, 4: 0, 5: 2, 6: 0, 7: 0, 8: 2, 9: 3, 10: 0, 11: 0, 12: 2, 13: 1, 14: 3, 15: 0, 16: 0,
        17: 0, 18: 0, 19: 0, 20: 0, 21: 3, 22: 3, 23: 3, 24: 3, 25: 2, 26: 3}
sec = {1: 1, 2: 1, 3: 2, 4: 1, 6: 1, 7: 1, 8: 1, 9: 0, 11: 1, 12: 1, 13: 0, 15: 1, 16: 1, 17: 1, 18: 1, 19: 2,
       20: 1, 23: 0, 24: 0}
for k, m in prim.items():
    M[m, k - 1] = 2
for k, m in sec.items():
    M[m, k - 1] = max(M[m, k - 1], 1)
fig, ax = plt.subplots(figsize=(11, 2.5), dpi=220)
ax.imshow(M, cmap=LinearSegmentedColormap.from_list('t', ['#f6f8fb', '#cfe0fb', '#2f80ed']), vmin=0, vmax=2, aspect='auto')
ax.set_xticks(range(26), specs, rotation=90, fontsize=9)
ax.set_yticks(range(4), methods)
ax.tick_params(length=0)
for x in np.arange(-.5, 26, 1):
    ax.axvline(x, color='white', lw=1.5)
for y in np.arange(-.5, 4, 1):
    ax.axhline(y, color='white', lw=1.5)
ax.axvline(9.5, color='#e58e0b', lw=2.5)
ax.text(4.5, -0.85, 'Required', ha='center', fontsize=10.5, color='#5b6675')
ax.text(17.5, -0.85, 'Desired', ha='center', fontsize=10.5, color='#5b6675')
fig.tight_layout(); fig.savefig('../Figures/heat_trace.pdf'); plt.close(fig)
print('done', np.round(tot, 2))
