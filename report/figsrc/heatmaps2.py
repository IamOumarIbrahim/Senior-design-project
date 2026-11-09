"""Heatmaps with SciencePlots + CMasher, following Rougier's emphasis rule:
colour only where the reader should look, grey for context, labels on the data instead of legends."""
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import scienceplots  # noqa: F401  (registers the styles)
import cmasher as cmr

plt.style.use(['science', 'no-latex'])
plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman'], 'mathtext.fontset': 'stix',
                     'font.size': 11, 'axes.linewidth': 0, 'xtick.major.size': 0, 'ytick.major.size': 0,
                     'xtick.minor.visible': False, 'ytick.minor.visible': False, 'xtick.top': False, 'ytick.right': False})
FOCUS = cmr.get_sub_cmap('cmr.arctic_r', 0.06, 0.62)      # white -> report blue
GREY = cmr.get_sub_cmap('cmr.neutral_r', 0.03, 0.30)      # paper -> light grey
CALM = cmr.get_sub_cmap('cmr.neutral_r', 0.03, 0.16)      # nearly flat context
INK, MUTED, ACCENT = '#1b2430', '#8a94a3', '#c81e1e'


def cell_text(ax, i, j, v, cmap, vmin, vmax, fmt, **kw):
    lum = np.dot(cmap((v - vmin) / (vmax - vmin))[:3], [0.299, 0.587, 0.114])
    ax.text(j, i, fmt.format(v), ha='center', va='center', color='white' if lum < 0.5 else INK, **kw)


# ------------------------------------------------------------------ 1. decision matrix
crit = ['Accuracy', 'Speed', 'Privacy', 'Cost', 'Power,\nheat', 'Install', 'Complexity', 'Availability']
w = np.array([.20, .18, .15, .14, .12, .08, .07, .06])
alts = ['A  On-device detection', 'B  Cloud-streamed vision', 'C  Landmark rules', 'D  Vehicle/wearable signals', 'E  Smartphone app']
S = np.array([[4, 4, 5, 4, 3, 4, 3, 4],
              [5, 2, 1, 2, 4, 3, 2, 4],
              [2, 5, 5, 4, 4, 4, 4, 4],
              [2, 5, 4, 2, 5, 2, 2, 3],
              [3, 3, 3, 5, 2, 5, 3, 5]], float)
tot = S @ w
order = np.argsort(-tot)                                  # best first, so the eye starts at the answer
S, alts, tot = S[order], [alts[k] for k in order], tot[order]

fig, ax = plt.subplots(figsize=(7.4, 2.75), dpi=220)
for i in range(len(alts)):
    cmap = FOCUS if i == 0 else GREY
    ax.imshow(np.ma.masked_where(np.broadcast_to(np.arange(len(alts))[:, None] != i, S.shape), S), cmap=cmap, vmin=1, vmax=5,
              aspect='auto', extent=(-.5, len(crit) - .5, len(alts) - .5, -.5))
    for j in range(len(crit)):
        cell_text(ax, i, j, S[i, j], cmap, 1, 5, '{:.0f}', fontsize=12 if i == 0 else 11)
# weights as a thin bar row above the matrix instead of text in the labels
for j, x in enumerate(w):
    ax.add_patch(plt.Rectangle((j - .4, -.62), .8 * x / w.max(), .1, color=MUTED, clip_on=False))
    ax.text(j - .4, -.7, f'{x * 100:.0f}%', fontsize=9, color=MUTED, va='bottom', ha='left')
for i, t in enumerate(tot):
    ax.text(len(crit) - .3, i, f'{t:.2f}', ha='left', va='center', fontsize=12.5 if i == 0 else 11,
            color=INK if i == 0 else MUTED, fontweight='bold' if i == 0 else 'normal')
ax.text(len(crit) - .3, -.66, 'score', fontsize=9, color=MUTED, va='bottom', ha='left')
ax.set_xticks(range(len(crit)), crit, fontsize=10.5)
ax.xaxis.set_ticks_position('bottom')
ax.set_yticks(range(len(alts)), alts)
for k, lab in enumerate(ax.get_yticklabels()):
    lab.set_color(INK if k == 0 else MUTED); lab.set_fontweight('bold' if k == 0 else 'normal')
ax.set_xlim(-.5, len(crit) + .35); ax.set_ylim(len(alts) - .5, -.75)
for s in ax.spines.values(): s.set_visible(False)
fig.tight_layout(); fig.savefig('../Figures/heat_decision.pdf'); plt.close(fig)

# ------------------------------------------------------------------ 2. where YOLO11n fails (measured, 3 seeds)
def rows(path, key):
    out = {}
    for r in csv.DictReader(open(path, encoding='utf8')):
        if r['model_id'] != 'yolo11n':
            continue
        out.setdefault(r[key], []).append([float(r['precision']), float(r['recall']), float(r['micro_f1'])])
    return {k: np.mean(v, 0) for k, v in out.items()}

cls = rows('operating_point_by_class.csv', 'class_name')
sub = rows('operating_point_by_subject.csv', 'subject')
cols = [('yawning', 'Yawning'), ('hand_over_mouth', 'Hand over\nmouth'), ('drinking', 'Drinking'), ('phone_use', 'Phone use')]
subs = sorted(sub)
M = np.array([cls[k] for k, _ in cols] + [sub[s] for s in subs]).T          # 3 metrics x 7 columns
xl = [n for _, n in cols] + [f'Driver {k + 1}' for k in range(len(subs))]
yl = ['Precision', 'Recall', 'F1']
weak = [(0, 1), (1, 5)]                                                     # look-alike precision, one hard driver
print('class/driver means\n', np.round(M, 3))

fig, ax = plt.subplots(figsize=(7.4, 2.75), dpi=220)
ax.imshow(M, cmap=CALM, vmin=0.4, vmax=1.0, aspect='auto')
mask = np.ones_like(M, bool)
for i, j in weak:
    mask[i, j] = False
ax.imshow(np.ma.masked_array(M, mask), cmap=matplotlib.colors.ListedColormap([ACCENT]), aspect='auto')
for i in range(M.shape[0]):
    for j in range(M.shape[1]):
        hot = (i, j) in weak
        ax.text(j, i, f'{M[i, j]:.2f}', ha='center', va='center', fontsize=12 if hot else 11,
                color='white' if hot else INK, fontweight='bold' if hot else 'normal')
ax.axvline(3.5, color='white', lw=5)
ax.set_xticks(range(len(xl)), xl, fontsize=10.5); ax.set_yticks(range(3), yl)
ax.text(1.5, -0.85, 'per class', ha='center', fontsize=10, color=MUTED)
ax.text(5.0, -0.85, 'per held-out driver', ha='center', fontsize=10, color=MUTED)
ax.annotate('look-alikes fool it,\nso: hard negatives', xy=(1, 0), xytext=(1.0, -1.45), ha='center', fontsize=10,
            color=ACCENT, annotation_clip=False)
ax.annotate('results depend on the driver,\nso: test on unseen drivers', xy=(5, 1), xytext=(5.0, 3.05), ha='center', va='top',
            fontsize=10, color=ACCENT, annotation_clip=False)
ax.set_ylim(2.5, -0.5)
for s in ax.spines.values(): s.set_visible(False)
fig.subplots_adjust(left=0.085, right=0.995, top=0.70, bottom=0.25)
fig.savefig('../Figures/heat_yolo_weak.pdf'); plt.close(fig)
